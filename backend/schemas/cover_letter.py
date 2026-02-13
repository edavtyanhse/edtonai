"""Schemas for cover letter generation API."""

from uuid import UUID

from pydantic import BaseModel, Field


class CoverLetterRequest(BaseModel):
    """Request to generate cover letter for resume version."""

    resume_version_id: UUID = Field(
        ...,
        description="ID of the resume version to generate cover letter for",
    )
    options: dict | None = Field(
        default=None,
        description="Optional generation options (reserved for future use)",
    )


class CoverLetterStructure(BaseModel):
    """Structure breakdown of the cover letter."""

    opening: str = Field(..., description="Opening paragraph")
    body: str = Field(..., description="Main argumentation")
    closing: str = Field(..., description="Closing paragraph")


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
