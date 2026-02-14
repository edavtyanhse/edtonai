"""Schemas for resume versions API."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class VersionCreateRequest(BaseModel):
    """Request to create a new version."""

    type: str = Field(..., description="Type of version: 'adapt' or 'ideal'")
    title: str | None = Field(None, max_length=255, description="User-friendly title")
    resume_text: str = Field(..., description="Original resume text")
    vacancy_text: str = Field(..., description="Vacancy text")
    result_text: str = Field(..., description="Result text (adapted or ideal resume)")
    change_log: list[dict[str, Any]] = Field(
        default_factory=list, description="Change log from adaptation"
    )
    selected_checkbox_ids: list[str] = Field(
        default_factory=list, description="Selected checkbox IDs"
    )
    analysis_id: UUID | None = Field(None, description="ID of the analysis used for adaptation")


class VersionItemResponse(BaseModel):
    """Summary item for version list."""

    id: str
    created_at: datetime
    type: str
    title: str | None = None

    class Config:
        from_attributes = True


class VersionDetailResponse(BaseModel):
    """Full version details."""

    id: str
    created_at: datetime
    type: str
    title: str | None = None
    resume_text: str
    vacancy_text: str
    result_text: str
    change_log: list[dict[str, Any]] = []

    class Config:
        from_attributes = True


class VersionListResponse(BaseModel):
    """Paginated list of versions."""

    items: list[VersionItemResponse]
    total: int
    limit: int
    offset: int
