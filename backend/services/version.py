"""Version service - user version history use cases."""

from typing import Any
from uuid import UUID

from backend.domain.version import (
    VersionDetailResult,
    VersionItemResult,
    VersionListResult,
)
from backend.errors.business import VersionNotFoundError
from backend.repositories.interfaces import IUserVersionRepository


class VersionService:
    """Application service for user version history."""

    def __init__(self, user_version_repo: IUserVersionRepository) -> None:
        self.user_version_repo = user_version_repo

    async def create_version(
        self,
        user_id: str | None,
        type: str,
        resume_text: str,
        vacancy_text: str,
        result_text: str,
        title: str | None = None,
        change_log: list[dict[str, Any]] | None = None,
        selected_checkbox_ids: list[str] | None = None,
        analysis_id: UUID | None = None,
    ) -> VersionDetailResult:
        """Create a new user-visible version."""
        version = await self.user_version_repo.create(
            user_id=user_id,
            type=type,
            title=title,
            resume_text=resume_text,
            vacancy_text=vacancy_text,
            result_text=result_text,
            change_log=change_log,
            selected_checkbox_ids=selected_checkbox_ids,
            analysis_id=analysis_id,
        )
        return self._to_detail(version)

    async def list_versions(
        self,
        user_id: str | None,
        limit: int = 50,
        offset: int = 0,
    ) -> VersionListResult:
        """List versions for the current user."""
        versions, total = await self.user_version_repo.list_versions(
            limit=limit,
            offset=offset,
            user_id=user_id,
        )
        return VersionListResult(
            items=[self._to_item(version) for version in versions],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def get_version(
        self,
        version_id: UUID,
        user_id: str | None,
    ) -> VersionDetailResult:
        """Get a single version owned by the current user."""
        version = await self.user_version_repo.get_by_id(version_id, user_id=user_id)
        if version is None:
            raise VersionNotFoundError(str(version_id))
        return self._to_detail(version)

    async def delete_version(self, version_id: UUID, user_id: str | None) -> None:
        """Delete a version owned by the current user."""
        deleted = await self.user_version_repo.delete_by_id(version_id, user_id=user_id)
        if not deleted:
            raise VersionNotFoundError(str(version_id))

    @staticmethod
    def _to_item(version: Any) -> VersionItemResult:
        return VersionItemResult(
            id=str(version.id),
            created_at=version.created_at,
            type=version.type,
            title=version.title,
            analysis_id=str(version.analysis_id) if version.analysis_id else None,
        )

    @staticmethod
    def _to_detail(version: Any) -> VersionDetailResult:
        return VersionDetailResult(
            id=str(version.id),
            created_at=version.created_at,
            type=version.type,
            title=version.title,
            resume_text=version.resume_text,
            vacancy_text=version.vacancy_text,
            result_text=version.result_text,
            change_log=version.change_log or [],
            selected_checkbox_ids=version.selected_checkbox_ids or [],
            analysis_id=str(version.analysis_id) if version.analysis_id else None,
        )
