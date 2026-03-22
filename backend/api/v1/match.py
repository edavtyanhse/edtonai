"""Match analysis endpoint."""

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_orchestrator_service
from backend.schemas import MatchAnalyzeRequest, MatchAnalyzeResponse
from backend.services import OrchestratorService

router = APIRouter(prefix="/match", tags=["match"])


@router.post("/analyze", response_model=MatchAnalyzeResponse)
async def analyze_match(
    request: MatchAnalyzeRequest,
    service: OrchestratorService = Depends(get_orchestrator_service),
) -> MatchAnalyzeResponse:
    """Analyze resume-vacancy match.

    Full pipeline:
    1. Parse resume (cached)
    2. Parse vacancy (cached)
    3. Analyze match (cached)

    Returns cache_hit=true only if ALL steps were from cache.
    """
    result = await service.run_analysis(
        request.resume_text,
        request.vacancy_text,
        original_analysis=request.original_analysis,
        applied_checkbox_ids=request.applied_checkbox_ids,
    )

    return MatchAnalyzeResponse(
        resume_id=result.resume_id,
        vacancy_id=result.vacancy_id,
        analysis_id=result.analysis_id,
        analysis=result.analysis,
        cache_hit=result.cache_hit,
    )
