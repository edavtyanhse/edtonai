"""Match response schemas."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class MatchAnalyzeResponse(BaseModel):
    """Response with match analysis data."""

    resume_id: UUID = Field(..., description="UUID of stored resume")
    vacancy_id: UUID = Field(..., description="UUID of stored vacancy")
    analysis_id: UUID = Field(..., description="UUID of analysis result")
    analysis: dict[str, Any] = Field(..., description="Match analysis JSON from LLM")
    cache_hit: bool = Field(..., description="True if all results were from cache")
