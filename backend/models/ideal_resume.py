"""IdealResume ORM model - generated ideal resume for vacancy."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class IdealResume(Base):
    """Ideal resume template generated for a specific vacancy.

    This is a reference example showing what an ideal candidate's resume
    would look like for the given vacancy. Used as inspiration/template,
    NOT as a real person's resume.
    """

    __tablename__ = "ideal_resume"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Link to vacancy this ideal resume was generated for
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vacancy_raw.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Hash of vacancy for quick cache lookup
    vacancy_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    # Full text of ideal resume
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Metadata from LLM: keywords_used, structure, assumptions, language, template
    generation_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Generation options used (language, template, seniority)
    options: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
    )

    # Hash for caching (includes vacancy_hash + options)
    input_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    # LLM metadata
    provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    prompt_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
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
    vacancy = relationship("VacancyRaw", foreign_keys=[vacancy_id])
