"""Vacancy repository for database operations."""

import logging
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from backend.domain.mappers import set_vacancy_parsed_data
from backend.models import VacancyRaw

logger = logging.getLogger(__name__)


class VacancyRepository:
    """Repository for VacancyRaw operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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

    async def update_parsed_data(
        self, vacancy_id: UUID, parsed_data: dict[str, Any]
    ) -> VacancyRaw | None:
        """Update parsed data columns for a vacancy."""
        vacancy = await self.get_by_id(vacancy_id)
        if vacancy is None:
            return None
        # Use helper method to set all parsed fields
        set_vacancy_parsed_data(vacancy, parsed_data)
        vacancy.parsed_at = datetime.utcnow()
        await self.session.flush()
        return vacancy

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
        vacancy.parsed_at = datetime.utcnow()
        await self.session.flush()
        return vacancy
