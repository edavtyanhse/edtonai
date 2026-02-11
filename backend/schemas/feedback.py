"""Feedback schemas for API requests/responses."""
from pydantic import BaseModel, Field
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Request schema for creating feedback."""
    feedback_text: str = Field(..., min_length=1, max_length=5000)


class FeedbackResponse(BaseModel):
    """Response schema for feedback submission."""
    id: int
    user_email: str
    feedback_text: str
    created_at: datetime

    class Config:
        from_attributes = True
