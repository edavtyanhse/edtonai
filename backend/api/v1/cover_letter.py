"""Cover Letter generation endpoints."""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_cover_letter_service
from backend.core.auth import get_current_user_id
from backend.schemas.cover_letter import (
    CoverLetterRequest,
    CoverLetterResponse,
    CoverLetterStructure,
)
from backend.services.cover_letter import CoverLetterService

router = APIRouter(tags=["cover-letter"])
logger = logging.getLogger(__name__)


@router.post(
    "/cover-letter",
    response_model=CoverLetterResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate cover letter for resume version",
    description="""
Generate professional cover letter based on:
- Specific resume version (adapted resume)
- Target vacancy
- Match analysis results

The cover letter will:
- Use only data from the resume version
- Address vacancy requirements
- Explain gaps or missing skills tactfully
- Be professional and ATS-friendly

Results are cached by (resume_version_text, vacancy_text, match_analysis).
    """,
)
async def generate_cover_letter(
    request: CoverLetterRequest,
    _user_id: str = Depends(get_current_user_id),
    cover_letter_service: CoverLetterService = Depends(get_cover_letter_service),
) -> CoverLetterResponse:
    """Generate cover letter for resume version.

    Requires:
    - resume_version_id must exist
    - resume_version must have analysis_id (match analysis)
    - vacancy must exist

    Returns generated cover letter with structure breakdown.
    """
    try:
        result = await cover_letter_service.generate_cover_letter(
            resume_version_id=request.resume_version_id,
            options=request.options or {},
        )

        return CoverLetterResponse(
            cover_letter_id=result.cover_letter_id,
            resume_version_id=result.resume_version_id,
            vacancy_id=result.vacancy_id,
            cover_letter_text=result.cover_letter_text,
            structure=CoverLetterStructure(
                opening=result.structure["opening"],
                body=result.structure["body"],
                closing=result.structure["closing"],
            ),
            key_points_used=result.key_points_used,
            alignment_notes=result.alignment_notes,
            cache_hit=result.cache_hit,
        )

    except ValueError as e:
        logger.warning("Cover letter generation failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(
            "Unexpected error during cover letter generation: %s",
            str(e),
            exc_info=True,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cover letter",
        ) from e
