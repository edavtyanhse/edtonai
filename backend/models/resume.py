"""ResumeRaw ORM model with structured parsed columns."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class ResumeRaw(Base):
    """
    Raw resume text with structured parsed data in separate columns.

    Each field from LLM parsing is stored in its own column for:
    - Better queryability
    - Easier partial updates
    - Schema validation at DB level
    """

    __tablename__ = "resume_raw"

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

    # ============ PARSED DATA COLUMNS ============

    # Personal info: {name, title, location, contacts: {email, phone, links}}
    personal_info: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Summary/About section (plain text)
    summary: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Skills: [{name, category, level}]
    skills: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # Work experience: [{company, position, start_date, end_date, responsibilities, achievements, tech_stack}]
    work_experience: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # Education: [{institution, degree, field, start_year, end_year}]
    education: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # Certifications: [{name, issuer, date}] or [str]
    certifications: Mapped[list[Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # Languages: [{language, proficiency}] or [str]
    languages: Mapped[list[Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
    )

    # Raw sections: {section_title: section_text}
    raw_sections: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
        default=dict,
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
