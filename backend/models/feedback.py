"""Feedback model for collecting user feedback."""

from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from backend.db.base import Base


class Feedback(Base):
    """User feedback submissions."""

    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    metric_type = Column(String(16), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    feedback_text = Column(Text, nullable=False)
    context_step = Column(String(64), nullable=True, index=True)
    ui_variant = Column(String(16), nullable=True, index=True)
    user_segment = Column(String(64), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
