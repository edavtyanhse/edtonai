"""Cover letter request schemas."""

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
