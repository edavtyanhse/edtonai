"""VacancyRaw ORM model with structured parsed columns."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class VacancyRaw(Base):
    """
    Raw vacancy text with structured parsed data in separate columns.

    Each field from LLM parsing is stored in its own column for:
    - Better queryability
    - Easier partial updates
    - Schema validation at DB level
    """

    __tablename__ = "vacancy_raw"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Original source text
    source_text: Mapped[str] = mapped_column(Text, nullable=False)
    content_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        index=True,
        nullable=False,
    )

    # URL the vacancy was fetched from (if any)
    source_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
    )

    # ============ PARSED DATA COLUMNS ============

    # Job title
    job_title: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Company name
    company: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Employment type (full-time, part-time, contract, etc.)
    employment_type: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Location
    location: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Required skills: [{name, type, evidence}]
    required_skills: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # Preferred skills: [{name, type, evidence}]
    preferred_skills: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # Experience requirements: {min_years, max_years, details}
    experience_requirements: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Responsibilities: [str]
    responsibilities: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # ATS keywords: [str]
    ats_keywords: Mapped[list[str] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # ============ METADATA ============

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
    parsed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
