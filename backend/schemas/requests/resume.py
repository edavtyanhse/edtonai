"""Resume request schemas."""

from pydantic import BaseModel, Field

from backend.core.config import MAX_RESUME_CHARS


class ResumeParseRequest(BaseModel):
    """Request to parse a resume."""

    resume_text: str = Field(
        ...,
        min_length=10,
        max_length=MAX_RESUME_CHARS,
        description="Raw resume text",
    )


class ResumePatchRequest(BaseModel):
    """Request to update parsed resume data."""

    parsed_data: dict = Field(
        ..., description="Updated structured resume data (partial or full)"
    )
