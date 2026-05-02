"""Ideal resume generation endpoint (Stage 2)."""

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_ideal_resume_service
from backend.core.auth import require_auth
from backend.schemas import IdealResumeMetadata, IdealResumeRequest, IdealResumeResponse
from backend.services import IdealResumeService

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/ideal", response_model=IdealResumeResponse)
async def generate_ideal_resume(
    request: IdealResumeRequest,
    user_id: str = Depends(require_auth),
    service: IdealResumeService = Depends(get_ideal_resume_service),
) -> IdealResumeResponse:
    """Generate an ideal resume template for a vacancy.

    This endpoint:
    1. Parses vacancy (uses cache if available)
    2. Generates ideal resume matching vacancy requirements
    3. Saves result to database for caching
    4. Returns generated resume with metadata

    Either vacancy_text or vacancy_id must be provided.

    The generated resume uses placeholder data (fake name, email etc.)
    and is meant as a reference/template, not a real person's resume.
    """
    # Validate that at least one vacancy source is provided
    if not request.vacancy_text and not request.vacancy_id:
        raise HTTPException(
            status_code=400,
            detail="Either vacancy_text or vacancy_id must be provided",
        )

    result = await service.generate_ideal(
        vacancy_text=request.vacancy_text,
        vacancy_id=request.vacancy_id,
        options=request.options.model_dump() if request.options else {},
        user_id=user_id,
    )

    return IdealResumeResponse(
        ideal_id=result.ideal_id,
        vacancy_id=result.vacancy_id,
        ideal_resume_text=result.ideal_resume_text,
        metadata=IdealResumeMetadata(**result.metadata)
        if result.metadata
        else IdealResumeMetadata(),
        cache_hit=result.cache_hit,
    )
