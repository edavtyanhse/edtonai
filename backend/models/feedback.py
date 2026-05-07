"""Feedback model for collecting user feedback."""

from datetime import datetime, timezone

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID

from backend.db.base import Base


class Feedback(Base):
    """User feedback submissions."""

    __tablename__ = "feedback"
    __table_args__ = (
        CheckConstraint("metric_type IN ('csat', 'nps')", name="ck_feedback_metric_type"),
        CheckConstraint(
            "(metric_type = 'csat' AND score BETWEEN 1 AND 5) "
            "OR (metric_type = 'nps' AND score BETWEEN 0 AND 10)",
            name="ck_feedback_score_by_metric",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    user_hash = Column(String(64), nullable=False, index=True)
    user_email = Column(String, nullable=True, index=True)
    metric_type = Column(String(16), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    feedback_text = Column(Text, nullable=False)
    context_step = Column(String(64), nullable=True, index=True)
    ui_variant = Column(String(16), nullable=True, index=True)
    user_segment = Column(String(64), nullable=True, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
