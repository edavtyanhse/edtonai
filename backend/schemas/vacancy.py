"""Vacancy parsing request/response schemas."""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class VacancyParseRequest(BaseModel):
    """Request to parse a vacancy."""

    vacancy_text: Optional[str] = Field(None, description="Raw vacancy text")
    url: Optional[str] = Field(None, description="URL to fetch vacancy from")
    
    # Custom validator could be added in pydantic v2 with @model_validator, 
    # but for simplicity we'll handle logical validation in the service/endpoint.



class VacancyParseResponse(BaseModel):
    """Response with parsed vacancy data."""

    vacancy_id: UUID = Field(..., description="UUID of stored vacancy")
    vacancy_hash: str = Field(..., description="SHA256 hash of normalized text")
    parsed_vacancy: dict[str, Any] = Field(..., description="Structured vacancy JSON from LLM")
    cache_hit: bool = Field(..., description="True if result was from cache")
    raw_text: str = Field(..., description="The raw vacancy text (either provided or scraped)")


class VacancyPatchRequest(BaseModel):
    """Request to update parsed vacancy data."""

    parsed_data: dict[str, Any] = Field(
        ..., description="Updated structured vacancy data (partial or full)"
    )


class VacancyDetailResponse(BaseModel):
    """Detailed vacancy response with all data."""

    id: UUID
    source_text: str
    content_hash: str
    parsed_data: Optional[dict[str, Any]] = None
    created_at: datetime
    parsed_at: Optional[datetime] = None
