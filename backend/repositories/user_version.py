"""Repository for UserVersion model."""

import logging
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models import UserVersion


class UserVersionRepository:
    """CRUD operations for UserVersion."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.logger = logging.getLogger(__name__)

    async def create(
        self,
        type: str,
        resume_text: str,
        vacancy_text: str,
        result_text: str,
        user_id: Optional[str] = None,
        title: Optional[str] = None,
        change_log: list[dict] = None,
        selected_checkbox_ids: list[str] = None,
        analysis_id: Optional[UUID] = None,
    ) -> UserVersion:
        """Create a new user version."""
        version = UserVersion(
            user_id=user_id,
            type=type,
            title=title,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            result_text=result_text,
            change_log=change_log or [],
            selected_checkbox_ids=selected_checkbox_ids or [],
            analysis_id=analysis_id,
        )
        self.session.add(version)
        await self.session.flush()
        self.logger.info("Created user version: %s for user: %s", version.id, user_id)
        return version

    async def get_by_id(
        self, version_id: UUID, user_id: Optional[str] = None
    ) -> Optional[UserVersion]:
        """Get user version by ID, optionally filtered by user_id."""
        query = select(UserVersion).where(UserVersion.id == version_id)
        
        # If user_id is provided, filter by it
        if user_id:
            query = query.where(UserVersion.user_id == user_id)
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_versions(
        self,
        limit: int = 50,
        offset: int = 0,
        user_id: Optional[str] = None,
    ) -> tuple[list[UserVersion], int]:
        """List versions with pagination, ordered by created_at desc.
        
        If user_id is provided, only returns versions for that user.
        """
        # Base query with optional user filter
        base_filter = UserVersion.user_id == user_id if user_id else True
        
        # Get total count
        count_result = await self.session.execute(
            select(func.count()).select_from(UserVersion).where(base_filter)
        )
        total = count_result.scalar_one()

        # Get paginated results
        result = await self.session.execute(
            select(UserVersion)
            .where(base_filter)
            .order_by(UserVersion.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        versions = list(result.scalars().all())

        return versions, total

    async def delete_by_id(
        self, version_id: UUID, user_id: Optional[str] = None
    ) -> bool:
        """Delete user version by ID. Returns True if deleted.
        
        If user_id is provided, only deletes if the version belongs to that user.
        """
        query = delete(UserVersion).where(UserVersion.id == version_id)
        
        if user_id:
            query = query.where(UserVersion.user_id == user_id)
        
        result = await self.session.execute(query)
        await self.session.flush()
        deleted = result.rowcount > 0
        if deleted:
            self.logger.info("Deleted user version: %s", version_id)
        return deleted
