"""Repository for ResumeVersion model."""

import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import ResumeVersion


class ResumeVersionRepository:
    """CRUD operations for ResumeVersion."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def create(
        self,
        resume_id: UUID,
        vacancy_id: UUID,
        text: str,
        change_log: list[dict],
        selected_checkbox_ids: list[str],
        analysis_id: UUID | None = None,
        parent_version_id: UUID | None = None,
        user_id: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        prompt_version: str | None = None,
    ) -> ResumeVersion:
        """Create a new resume version."""
        version = ResumeVersion(
            resume_id=resume_id,
            vacancy_id=vacancy_id,
            text=text,
            change_log=change_log,
            selected_checkbox_ids=selected_checkbox_ids,
            analysis_id=analysis_id,
            parent_version_id=parent_version_id,
            user_id=user_id,
            provider=provider,
            model=model,
            prompt_version=prompt_version,
        )
        self.session.add(version)
        await self.session.flush()
        self.logger.info("Created resume version: %s", version.id)
        return version

    async def get_by_id(self, version_id: UUID) -> ResumeVersion | None:
        """Get resume version by ID."""
        result = await self.session.execute(
            select(ResumeVersion).where(ResumeVersion.id == version_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_for_user(
        self, version_id: UUID, user_id: str
    ) -> ResumeVersion | None:
        """Get resume version by ID only if it belongs to the given user."""
        result = await self.session.execute(
            select(ResumeVersion).where(
                ResumeVersion.id == version_id,
                ResumeVersion.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_versions_for_resume(
        self,
        resume_id: UUID,
        vacancy_id: UUID | None = None,
    ) -> list[ResumeVersion]:
        """Get all versions for a resume, optionally filtered by vacancy."""
        query = select(ResumeVersion).where(ResumeVersion.resume_id == resume_id)
        if vacancy_id:
            query = query.where(ResumeVersion.vacancy_id == vacancy_id)
        query = query.order_by(ResumeVersion.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_latest_version(
        self,
        resume_id: UUID,
        vacancy_id: UUID,
    ) -> ResumeVersion | None:
        """Get the most recent version for resume-vacancy pair."""
        result = await self.session.execute(
            select(ResumeVersion)
            .where(ResumeVersion.resume_id == resume_id)
            .where(ResumeVersion.vacancy_id == vacancy_id)
            .order_by(ResumeVersion.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
