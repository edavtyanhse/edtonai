"""Feedback response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    user_email: str
    feedback_text: str
    created_at: datetime
