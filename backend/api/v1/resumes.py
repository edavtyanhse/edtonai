"""Resume parsing endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_resume_service
from backend.schemas import (
    ResumeDetailResponse,
    ResumeParseRequest,
    ResumeParseResponse,
    ResumePatchRequest,
)
from backend.services import ResumeService

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    request: ResumeParseRequest,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeParseResponse:
    """Parse resume text and return structured data.

    - Caches results by content hash
    - Returns cache_hit=true if result was from cache
    """
    result = await service.parse_and_cache(request.resume_text)

    return ResumeParseResponse(
        resume_id=result.resume_id,
        resume_hash=result.resume_hash,
        parsed_resume=result.parsed_resume,
        cache_hit=result.cache_hit,
    )


@router.get("/{resume_id}", response_model=ResumeDetailResponse)
async def get_resume(
    resume_id: UUID,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeDetailResponse:
    """Get resume by ID with all details."""
    resume = await service.get_detail(resume_id)

    return ResumeDetailResponse(
        id=resume.id,
        source_text=resume.source_text,
        content_hash=resume.content_hash,
        parsed_data=resume.parsed_data,
        created_at=resume.created_at,
        parsed_at=resume.parsed_at,
    )


@router.patch("/{resume_id}", response_model=ResumeDetailResponse)
async def update_resume_parsed_data(
    resume_id: UUID,
    request: ResumePatchRequest,
    service: ResumeService = Depends(get_resume_service),
) -> ResumeDetailResponse:
    """Update parsed data for a resume.

    Allows frontend to save edited structured resume fields.
    This is separate from the wizard navigation (Next button).
    """
    resume = await service.update_parsed_data(resume_id, request.parsed_data)

    return ResumeDetailResponse(
        id=resume.id,
        source_text=resume.source_text,
        content_hash=resume.content_hash,
        parsed_data=resume.parsed_data,
        created_at=resume.created_at,
        parsed_at=resume.parsed_at,
    )
