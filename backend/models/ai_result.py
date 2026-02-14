"""AIResult ORM model - universal LLM cache table."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from backend.db.base import Base


class AIResult(Base):
    """Cache for LLM operation results.

    Stores parsed resumes, vacancies, and match analyses.
    Unique constraint on (operation, input_hash) prevents duplicate calls.
    """

    __tablename__ = "ai_result"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    operation: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        comment="parse_resume | parse_vacancy | analyze_match",
    )
    input_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )
    output_json: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
    )
    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )
    provider: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    error: Mapped[str | None] = mapped_column(
        Text,
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

    __table_args__ = (
        Index(
            "ix_ai_result_operation_input_hash",
            "operation",
            "input_hash",
            unique=True,
        ),
    )
