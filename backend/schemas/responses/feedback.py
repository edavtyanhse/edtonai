"""Feedback response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_email: str
    metric_type: str
    score: int
    feedback_text: str
    context_step: str | None
    ui_variant: str | None
    user_segment: str | None
    created_at: datetime
