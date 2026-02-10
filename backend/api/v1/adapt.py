"""Resume adaptation endpoint (Stage 2)."""

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_adapt_resume_service
from backend.ai.errors import AIError
from backend.schemas import AdaptResumeRequest, AdaptResumeResponse, ChangeLogEntry
from backend.services import AdaptResumeService
from backend.services.adapt import SelectedImprovement

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/adapt", response_model=AdaptResumeResponse)
async def adapt_resume(
    request: AdaptResumeRequest,
    service: AdaptResumeService = Depends(get_adapt_resume_service),
) -> AdaptResumeResponse:
    """Adapt resume for a vacancy based on selected improvements.

    This endpoint:
    1. Parses resume and vacancy (uses cache if available)
    2. Gets match analysis (uses cache if available)
    3. Generates adapted resume applying selected checkbox improvements
    4. Saves new resume version to database
    5. Returns adapted text with change log

    Either resume_text or resume_id must be provided.
    Either vacancy_text or vacancy_id must be provided.
    selected_improvements should contain improvements with optional user_input.
    """
    # Validate that at least one resume source is provided
    if not request.resume_text and not request.resume_id:
        raise HTTPException(
            status_code=400,
            detail="Either resume_text or resume_id must be provided",
        )

    # Validate that at least one vacancy source is provided
    if not request.vacancy_text and not request.vacancy_id:
        raise HTTPException(
            status_code=400,
            detail="Either vacancy_text or vacancy_id must be provided",
        )
    
    # Validate that at least one improvement is selected
    has_improvements = bool(request.selected_improvements) or bool(request.selected_checkbox_ids)
    if not has_improvements:
        raise HTTPException(
            status_code=400,
            detail="At least one improvement must be selected (use selected_improvements or selected_checkbox_ids)",
        )

    # Convert request improvements to service format
    selected_improvements = None
    if request.selected_improvements:
        selected_improvements = [
            SelectedImprovement(
                checkbox_id=imp.checkbox_id,
                user_input=imp.user_input,
                ai_generate=imp.ai_generate,
            )
            for imp in request.selected_improvements
        ]

    try:
        result = await service.adapt_and_version(
            resume_text=request.resume_text,
            resume_id=request.resume_id,
            vacancy_text=request.vacancy_text,
            vacancy_id=request.vacancy_id,
            selected_improvements=selected_improvements,
            selected_checkbox_ids=request.selected_checkbox_ids,  # Legacy support
            base_version_id=request.base_version_id,
            options=request.options.model_dump() if request.options else {},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except AIError as e:
        raise HTTPException(status_code=502, detail=f"AI provider error: {e}")

    return AdaptResumeResponse(
        version_id=result.version_id,
        parent_version_id=result.parent_version_id,
        resume_id=result.resume_id,
        vacancy_id=result.vacancy_id,
        updated_resume_text=result.updated_resume_text,
        change_log=[ChangeLogEntry(**entry) for entry in result.change_log],
        applied_checkbox_ids=result.applied_checkbox_ids,
        cache_hit=result.cache_hit,
    )
