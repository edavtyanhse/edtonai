"""Cover Letter generation endpoints."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.dependencies import get_cover_letter_service
from backend.core.auth import require_auth
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
    user_id: str = Depends(require_auth),
    cover_letter_service: CoverLetterService = Depends(get_cover_letter_service),
) -> CoverLetterResponse:
    """Generate cover letter for resume version.

    Requires:
    - resume_version_id must exist
    - resume_version must have analysis_id (match analysis)
    - vacancy must exist (or be embedded in UserVersion)
    - authenticated user must own the resume version

    Returns generated cover letter with structure breakdown.
    """
    try:
        result = await cover_letter_service.generate_cover_letter(
            resume_version_id=request.resume_version_id,
            user_id=user_id,
            options=request.options or {},
        )

        structure = result.structure or {}
        return CoverLetterResponse(
            cover_letter_id=result.cover_letter_id,
            resume_version_id=result.resume_version_id,
            vacancy_id=result.vacancy_id,
            cover_letter_text=result.cover_letter_text,
            structure=CoverLetterStructure(
                opening=structure.get("opening", ""),
                body=structure.get("body", ""),
                closing=structure.get("closing", ""),
            ),
            key_points_used=result.key_points_used,
            alignment_notes=result.alignment_notes,
            cache_hit=result.cache_hit,
        )

    except ValueError as e:
        logger.warning("Cover letter generation failed: %s", str(e))
        msg = str(e)
        msg_l = msg.lower()
        if "not found" in msg_l:
            status_code = status.HTTP_404_NOT_FOUND
        elif "access denied" in msg_l:
            status_code = status.HTTP_403_FORBIDDEN
        else:
            status_code = status.HTTP_400_BAD_REQUEST
        raise HTTPException(
            status_code=status_code,
            detail=msg,
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
