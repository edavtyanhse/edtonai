"""Resume request schemas."""

from pydantic import BaseModel, Field


class ResumeParseRequest(BaseModel):
    """Request to parse a resume."""

    resume_text: str = Field(..., min_length=10, description="Raw resume text")


class ResumePatchRequest(BaseModel):
    """Request to update parsed resume data."""

    parsed_data: dict = Field(
        ..., description="Updated structured resume data (partial or full)"
    )
