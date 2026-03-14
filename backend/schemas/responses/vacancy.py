"""Vacancy response schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class VacancyParseResponse(BaseModel):
    """Response with parsed vacancy data."""

    vacancy_id: UUID = Field(..., description="UUID of stored vacancy")
    vacancy_hash: str = Field(..., description="SHA256 hash of normalized text")
    parsed_vacancy: dict[str, Any] = Field(..., description="Structured vacancy JSON from LLM")
    cache_hit: bool = Field(..., description="True if result was from cache")
    raw_text: str = Field(..., description="The raw vacancy text (either provided or scraped)")


class VacancyDetailResponse(BaseModel):
    """Detailed vacancy response with all data."""

    id: UUID
    source_text: str
    content_hash: str
    parsed_data: dict[str, Any] | None = None
    created_at: datetime
    parsed_at: datetime | None = None
