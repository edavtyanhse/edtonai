"""UserVersion ORM model - simplified version storage for frontend."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class UserVersion(Base):
    """Standalone version storage for frontend history feature.

    Unlike ResumeVersion, this doesn't require foreign keys to parsed documents.
    It stores the raw text inputs and result for easy retrieval.
    """

    __tablename__ = "user_version"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # User ID from Supabase Auth (for per-user filtering)
    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Type: 'adapt' or 'ideal'
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    # Reference to analysis result (for cover letter generation)
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_result.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # User-friendly title
    title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Original resume text
    resume_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Vacancy text used for adaptation
    vacancy_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Result text (adapted or ideal resume)
    result_text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Change log from adaptation
    change_log: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Selected checkbox IDs for this adaptation
    selected_checkbox_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    # Relationships
    analysis = relationship(
        "backend.models.ai_result.AIResult", foreign_keys=[analysis_id]
    )
