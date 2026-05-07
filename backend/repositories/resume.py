"""Resume repository for database operations."""

import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.mappers import set_resume_parsed_data
from backend.models import ResumeRaw, UserResume

logger = logging.getLogger(__name__)


class ResumeRepository:
    """Repository for ResumeRaw operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _user_uuid(user_id: str | UUID) -> UUID:
        return user_id if isinstance(user_id, UUID) else UUID(user_id)

    @staticmethod
    def _with_user_override(resume: ResumeRaw, link: UserResume) -> Any:
        """Return a detached snapshot with user-specific parsed overrides applied."""
        snapshot = SimpleNamespace(
            id=resume.id,
            source_text=resume.source_text,
            content_hash=resume.content_hash,
            personal_info=resume.personal_info,
            summary=resume.summary,
            skills=resume.skills,
            work_experience=resume.work_experience,
            education=resume.education,
            certifications=resume.certifications,
            languages=resume.languages,
            raw_sections=resume.raw_sections,
            created_at=resume.created_at,
            updated_at=resume.updated_at,
            parsed_at=link.parsed_at or resume.parsed_at,
        )
        if link.parsed_data_override:
            set_resume_parsed_data(snapshot, link.parsed_data_override)
        return snapshot

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

    async def get_by_id_for_user(
        self,
        resume_id: UUID,
        user_id: str | UUID,
    ) -> Any | None:
        """Get resume by ID only if it is linked to the given user."""
        user_uuid = self._user_uuid(user_id)
        stmt = (
            select(ResumeRaw, UserResume)
            .join(UserResume, UserResume.resume_id == ResumeRaw.id)
            .where(ResumeRaw.id == resume_id, UserResume.user_id == user_uuid)
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        resume, link = row
        return self._with_user_override(resume, link)

    async def create(self, source_text: str, content_hash: str) -> ResumeRaw:
        """Create new resume record."""
        resume = ResumeRaw(source_text=source_text, content_hash=content_hash)
        self.session.add(resume)
        await self.session.flush()
        return resume

    async def get_or_create(self, source_text: str, content_hash: str) -> ResumeRaw:
        """Get existing resume by hash or create new one.

        Uses a savepoint (begin_nested) so that IntegrityError on duplicate
        hash rolls back only the INSERT, keeping the session usable.
        """
        existing = await self.get_by_hash(content_hash)
        if existing is not None:
            return existing

        try:
            async with self.session.begin_nested():
                resume = ResumeRaw(source_text=source_text, content_hash=content_hash)
                self.session.add(resume)
            # flush happened inside begin_nested commit
            return resume
        except IntegrityError:
            logger.info("Race condition on resume content_hash, re-fetching")
            existing = await self.get_by_hash(content_hash)
            if existing is not None:
                return existing
            raise

    async def link_user_resume(self, user_id: str | UUID, resume_id: UUID) -> None:
        """Link an existing raw resume record to a user."""
        user_uuid = self._user_uuid(user_id)
        if await self.user_has_access(user_id, resume_id):
            return
        try:
            async with self.session.begin_nested():
                self.session.add(UserResume(user_id=user_uuid, resume_id=resume_id))
        except IntegrityError:
            logger.info("Race condition on user_resume link, ignoring duplicate")

    async def user_has_access(self, user_id: str | UUID, resume_id: UUID) -> bool:
        """Return True if the user owns or has created this resume record."""
        user_uuid = self._user_uuid(user_id)
        stmt = select(UserResume.id).where(
            UserResume.user_id == user_uuid,
            UserResume.resume_id == resume_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update_parsed_data(
        self, resume_id: UUID, parsed_data: dict[str, Any]
    ) -> ResumeRaw | None:
        """Update parsed data columns for a resume."""
        resume = await self.get_by_id(resume_id)
        if resume is None:
            return None
        # Use helper method to set all parsed fields
        set_resume_parsed_data(resume, parsed_data)
        resume.parsed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return resume

    async def update_parsed_data_for_user(
        self,
        resume_id: UUID,
        user_id: str | UUID,
        parsed_data: dict[str, Any],
    ) -> Any | None:
        """Store user-specific parsed data without mutating the shared raw cache."""
        user_uuid = self._user_uuid(user_id)
        result = await self.session.execute(
            select(ResumeRaw, UserResume)
            .join(UserResume, UserResume.resume_id == ResumeRaw.id)
            .where(ResumeRaw.id == resume_id, UserResume.user_id == user_uuid)
        )
        row = result.one_or_none()
        if row is None:
            return None
        resume, link = row
        link.parsed_data_override = parsed_data
        link.parsed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return self._with_user_override(resume, link)

    async def update_field(
        self, resume_id: UUID, field: str, value: Any
    ) -> ResumeRaw | None:
        """Update a single parsed field for a resume."""
        resume = await self.get_by_id(resume_id)
        if resume is None:
            return None

        allowed_fields = [
            "personal_info",
            "summary",
            "skills",
            "work_experience",
            "education",
            "certifications",
            "languages",
            "raw_sections",
        ]
        if field not in allowed_fields:
            raise ValueError(f"Field {field} is not allowed")

        setattr(resume, field, value)
        resume.parsed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return resume
