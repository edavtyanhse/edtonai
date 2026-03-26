"""Resume repository for database operations."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.mappers import set_resume_parsed_data
from backend.models import ResumeRaw

logger = logging.getLogger(__name__)


class ResumeRepository:
    """Repository for ResumeRaw operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_hash(self, content_hash: str) -> ResumeRaw | None:
        """Get resume by content hash."""
        stmt = select(ResumeRaw).where(ResumeRaw.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, resume_id: UUID) -> ResumeRaw | None:
        """Get resume by ID."""
        stmt = select(ResumeRaw).where(ResumeRaw.id == resume_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, source_text: str, content_hash: str) -> ResumeRaw:
        """Create new resume record."""
        resume = ResumeRaw(source_text=source_text, content_hash=content_hash)
        self.session.add(resume)
        await self.session.flush()
        return resume

    async def get_or_create(self, source_text: str, content_hash: str) -> ResumeRaw:
        """Get existing resume by hash or create new one.

        Handles race condition when parallel requests try to create
        a resume with the same content_hash concurrently.
        """
        existing = await self.get_by_hash(content_hash)
        if existing is not None:
            return existing

        try:
            return await self.create(source_text, content_hash)
        except IntegrityError:
            logger.info("Race condition on content_hash, rolling back and re-fetching")
            await self.session.rollback()
            existing = await self.get_by_hash(content_hash)
            if existing is not None:
                return existing
            raise  # Should not happen, but re-raise if it does

    async def update_parsed_data(
        self, resume_id: UUID, parsed_data: dict[str, Any]
    ) -> ResumeRaw | None:
        """Update parsed data columns for a resume."""
        resume = await self.get_by_id(resume_id)
        if resume is None:
            return None
        # Use helper method to set all parsed fields
        set_resume_parsed_data(resume, parsed_data)
        resume.parsed_at = datetime.utcnow()
        await self.session.flush()
        return resume

    async def update_field(
        self, resume_id: UUID, field: str, value: Any
    ) -> ResumeRaw | None:
        """Update a single parsed field for a resume."""
        resume = await self.get_by_id(resume_id)
        if resume is None:
            return None

        allowed_fields = [
            "personal_info", "summary", "skills", "work_experience",
            "education", "certifications", "languages", "raw_sections"
        ]
        if field not in allowed_fields:
            raise ValueError(f"Field {field} is not allowed")

        setattr(resume, field, value)
        resume.parsed_at = datetime.utcnow()
        await self.session.flush()
        return resume
