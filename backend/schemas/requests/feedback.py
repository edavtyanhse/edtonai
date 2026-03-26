"""Feedback request schemas."""

from typing import Literal

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    """Request schema for creating feedback."""

    metric_type: Literal["csat", "nps"] = Field(
        ..., description="Type of metric: csat (1-5) or nps (0-10)"
    )
    score: int = Field(..., ge=0, le=10, description="Metric score value")
    feedback_text: str = Field(..., min_length=1, max_length=5000)
    context_step: str | None = Field(
        None, max_length=64, description="Product step where feedback was requested"
    )
    ui_variant: str | None = Field(
        None, max_length=16, description="A/B UI variant (e.g. A, B)"
    )
    user_segment: str | None = Field(
        None, max_length=64, description="User segment label for analytics"
    )
