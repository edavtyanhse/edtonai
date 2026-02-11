"""Feedback model for collecting user feedback."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from backend.db.base import Base


class Feedback(Base):
    """User feedback submissions."""
    
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, nullable=False, index=True)
    feedback_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
