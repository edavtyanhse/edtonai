"""Resume response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class ResumeParseResponse(BaseModel):
    """Response with parsed resume data."""

    resume_id: UUID = Field(..., description="UUID of stored resume")
    resume_hash: str = Field(..., description="SHA256 hash of normalized text")
    parsed_resume: dict[str, Any] = Field(..., description="Structured resume JSON from LLM")
    cache_hit: bool = Field(..., description="True if result was from cache")


class ResumeDetailResponse(BaseModel):
    """Detailed resume response with all data."""

    id: UUID
    source_text: str
    content_hash: str
    parsed_data: dict[str, Any] | None = None
    created_at: datetime
    parsed_at: datetime | None = None
