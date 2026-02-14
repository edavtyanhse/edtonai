"""Repository for IdealResume model."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import IdealResume


class IdealResumeRepository:
    """CRUD operations for IdealResume."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def create(
        self,
        vacancy_id: UUID,
        vacancy_hash: str,
        text: str,
        generation_metadata: dict,
        options: dict,
        input_hash: str,
        provider: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> IdealResume:
        """Create a new ideal resume record."""
        ideal = IdealResume(
            vacancy_id=vacancy_id,
            vacancy_hash=vacancy_hash,
            text=text,
            generation_metadata=generation_metadata,
            options=options,
            input_hash=input_hash,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
        )
        self.session.add(ideal)
        await self.session.flush()
        self.logger.info("Created ideal resume: %s", ideal.id)
        return ideal

    async def get_by_id(self, ideal_id: UUID) -> IdealResume | None:
        """Get ideal resume by ID."""
        result = await self.session.execute(
            select(IdealResume).where(IdealResume.id == ideal_id)
        )
        return result.scalar_one_or_none()

    async def get_by_input_hash(self, input_hash: str) -> IdealResume | None:
        """Get ideal resume by input hash (for cache lookup)."""
        result = await self.session.execute(
            select(IdealResume).where(IdealResume.input_hash == input_hash)
        )
        return result.scalar_one_or_none()

    async def get_for_vacancy(self, vacancy_id: UUID) -> list[IdealResume]:
        """Get all ideal resumes generated for a vacancy."""
        result = await self.session.execute(
            select(IdealResume)
            .where(IdealResume.vacancy_id == vacancy_id)
            .order_by(IdealResume.created_at.desc())
        )
        return list(result.scalars().all())
