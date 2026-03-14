"""Match request schemas."""

from pydantic import BaseModel, Field


class MatchAnalyzeRequest(BaseModel):
    """Request to analyze resume-vacancy match."""

    resume_text: str = Field(..., min_length=10, description="Raw resume text")
    vacancy_text: str = Field(..., min_length=10, description="Raw vacancy text")
