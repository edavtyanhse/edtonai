"""ResumeVersion ORM model - history of resume adaptations."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class ResumeVersion(Base):
    """Version of adapted resume with change history.

    Stores:
    - Full text of the adapted resume
    - Change log from LLM (what was changed and where)
    - Reference to parent version for history/rollback
    - Selected checkbox IDs that user chose for adaptation
    """

    __tablename__ = "resume_version"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )

    # Link to base resume document
    resume_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_raw.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Link to vacancy this version was adapted for
    vacancy_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("vacancy_raw.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Parent version for history chain (null = first adaptation from original)
    parent_version_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resume_version.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Owner for security-sensitive access to generated versions
    user_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=True,
    )

    # Full adapted resume text
    text: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Change log from LLM: [{checkbox_id, what_changed, where, before_excerpt, after_excerpt}]
    change_log: Mapped[list[dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Checkbox IDs selected by user for this adaptation
    selected_checkbox_ids: Mapped[list[str]] = mapped_column(
        JSONB,
        nullable=False,
        default=list,
    )

    # Reference to analysis result that was used for adaptation
    analysis_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ai_result.id", ondelete="SET NULL"),
        nullable=True,
    )

    # LLM metadata
    provider: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    model: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )
    prompt_version: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        comment="Version tag of the prompt used",
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
    resume = relationship("ResumeRaw", foreign_keys=[resume_id])
    vacancy = relationship("VacancyRaw", foreign_keys=[vacancy_id])
    parent_version = relationship(
        "ResumeVersion", remote_side=[id], foreign_keys=[parent_version_id]
    )
    analysis = relationship("AIResult", foreign_keys=[analysis_id])
