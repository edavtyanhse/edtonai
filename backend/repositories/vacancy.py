"""Vacancy repository for database operations."""

import logging
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.mappers import set_vacancy_parsed_data
from backend.models import UserVacancy, VacancyRaw

logger = logging.getLogger(__name__)


class VacancyRepository:
    """Repository for VacancyRaw operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    @staticmethod
    def _user_uuid(user_id: str | UUID) -> UUID:
        return user_id if isinstance(user_id, UUID) else UUID(user_id)

    @staticmethod
    def _with_user_override(vacancy: VacancyRaw, link: UserVacancy) -> Any:
        """Return a detached snapshot with user-specific parsed overrides applied."""
        snapshot = SimpleNamespace(
            id=vacancy.id,
            source_text=vacancy.source_text,
            content_hash=vacancy.content_hash,
            source_url=vacancy.source_url,
            job_title=vacancy.job_title,
            company=vacancy.company,
            employment_type=vacancy.employment_type,
            location=vacancy.location,
            required_skills=vacancy.required_skills,
            preferred_skills=vacancy.preferred_skills,
            experience_requirements=vacancy.experience_requirements,
            responsibilities=vacancy.responsibilities,
            ats_keywords=vacancy.ats_keywords,
            created_at=vacancy.created_at,
            updated_at=vacancy.updated_at,
            parsed_at=link.parsed_at or vacancy.parsed_at,
        )
        if link.parsed_data_override:
            set_vacancy_parsed_data(snapshot, link.parsed_data_override)
        return snapshot

    async def get_by_hash(self, content_hash: str) -> VacancyRaw | None:
        """Get vacancy by content hash."""
        stmt = select(VacancyRaw).where(VacancyRaw.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, vacancy_id: UUID) -> VacancyRaw | None:
        """Get vacancy by ID."""
        stmt = select(VacancyRaw).where(VacancyRaw.id == vacancy_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self,
        vacancy_id: UUID,
        user_id: str | UUID,
    ) -> Any | None:
        """Get vacancy by ID only if it is linked to the given user."""
        user_uuid = self._user_uuid(user_id)
        stmt = (
            select(VacancyRaw, UserVacancy)
            .join(UserVacancy, UserVacancy.vacancy_id == VacancyRaw.id)
            .where(VacancyRaw.id == vacancy_id, UserVacancy.user_id == user_uuid)
        )
        result = await self.session.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        vacancy, link = row
        return self._with_user_override(vacancy, link)

    async def create(
        self,
        source_text: str,
        content_hash: str,
        source_url: str | None = None,
    ) -> VacancyRaw:
        """Create new vacancy record."""
        vacancy = VacancyRaw(
            source_text=source_text,
            content_hash=content_hash,
            source_url=source_url,
        )
        self.session.add(vacancy)
        await self.session.flush()
        return vacancy

    async def get_or_create(
        self,
        source_text: str,
        content_hash: str,
        source_url: str | None = None,
    ) -> VacancyRaw:
        """Get existing vacancy by hash or create new one.

        Uses a savepoint (begin_nested) so that IntegrityError on duplicate
        hash rolls back only the INSERT, keeping the session usable.
        """
        existing = await self.get_by_hash(content_hash)
        if existing is not None:
            return existing

        try:
            async with self.session.begin_nested():
                vacancy = VacancyRaw(
                    source_text=source_text,
                    content_hash=content_hash,
                    source_url=source_url,
                )
                self.session.add(vacancy)
            return vacancy
        except IntegrityError:
            logger.info("Race condition on vacancy content_hash, re-fetching")
            existing = await self.get_by_hash(content_hash)
            if existing is not None:
                return existing
            raise

    async def link_user_vacancy(self, user_id: str | UUID, vacancy_id: UUID) -> None:
        """Link an existing raw vacancy record to a user."""
        user_uuid = self._user_uuid(user_id)
        if await self.user_has_access(user_id, vacancy_id):
            return
        try:
            async with self.session.begin_nested():
                self.session.add(
                    UserVacancy(user_id=user_uuid, vacancy_id=vacancy_id)
                )
        except IntegrityError:
            logger.info("Race condition on user_vacancy link, ignoring duplicate")

    async def user_has_access(self, user_id: str | UUID, vacancy_id: UUID) -> bool:
        """Return True if the user owns or has created this vacancy record."""
        user_uuid = self._user_uuid(user_id)
        stmt = select(UserVacancy.id).where(
            UserVacancy.user_id == user_uuid,
            UserVacancy.vacancy_id == vacancy_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def update_parsed_data(
        self, vacancy_id: UUID, parsed_data: dict[str, Any]
    ) -> VacancyRaw | None:
        """Update parsed data columns for a vacancy."""
        vacancy = await self.get_by_id(vacancy_id)
        if vacancy is None:
            return None
        # Use helper method to set all parsed fields
        set_vacancy_parsed_data(vacancy, parsed_data)
        vacancy.parsed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return vacancy

    async def update_parsed_data_for_user(
        self,
        vacancy_id: UUID,
        user_id: str | UUID,
        parsed_data: dict[str, Any],
    ) -> Any | None:
        """Store user-specific parsed data without mutating the shared raw cache."""
        user_uuid = self._user_uuid(user_id)
        result = await self.session.execute(
            select(VacancyRaw, UserVacancy)
            .join(UserVacancy, UserVacancy.vacancy_id == VacancyRaw.id)
            .where(VacancyRaw.id == vacancy_id, UserVacancy.user_id == user_uuid)
        )
        row = result.one_or_none()
        if row is None:
            return None
        vacancy, link = row
        link.parsed_data_override = parsed_data
        link.parsed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return self._with_user_override(vacancy, link)

    async def update_field(
        self, vacancy_id: UUID, field: str, value: Any
    ) -> VacancyRaw | None:
        """Update a single parsed field for a vacancy."""
        vacancy = await self.get_by_id(vacancy_id)
        if vacancy is None:
            return None

        allowed_fields = [
            "job_title",
            "company",
            "employment_type",
            "location",
            "required_skills",
            "preferred_skills",
            "experience_requirements",
            "responsibilities",
            "ats_keywords",
        ]
        if field not in allowed_fields:
            raise ValueError(f"Field {field} is not allowed")

        setattr(vacancy, field, value)
        vacancy.parsed_at = datetime.now(timezone.utc)
        await self.session.flush()
        return vacancy
