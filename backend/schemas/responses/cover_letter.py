"""Cover letter response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.common import CoverLetterStructure


class CoverLetterResponse(BaseModel):
    """Response with generated cover letter."""

    cover_letter_id: UUID = Field(
        ...,
        description="ID of the AI result (for caching)",
    )
    resume_version_id: UUID = Field(
        ...,
        description="ID of the resume version used",
    )
    vacancy_id: UUID | None = Field(
        None,
        description="ID of the vacancy (if linked)",
    )
    cover_letter_text: str = Field(
        ...,
        description="Full text of the cover letter",
    )
    structure: CoverLetterStructure = Field(
        ...,
        description="Breakdown of cover letter structure",
    )
    key_points_used: list[str] = Field(
        ...,
        description="Skills and facts from resume that were used",
    )
    alignment_notes: list[str] = Field(
        ...,
        description="How letter addresses vacancy requirements and gaps",
    )
    cache_hit: bool = Field(
        ...,
        description="Whether result was retrieved from cache",
    )
