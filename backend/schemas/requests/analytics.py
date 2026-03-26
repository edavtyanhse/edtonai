"""Analytics event request schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AnalyticsEventCreate(BaseModel):
    """Request schema for product analytics event ingestion."""

    event_name: str = Field(..., min_length=1, max_length=64)
    session_id: str = Field(..., min_length=1, max_length=128)
    step: str | None = Field(None, max_length=64)
    ui_variant: str | None = Field(None, max_length=16)
    user_segment: str | None = Field(None, max_length=64)
    occurred_at: datetime | None = None
    properties: dict[str, Any] = Field(default_factory=dict)
