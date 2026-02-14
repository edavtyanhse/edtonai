"""API endpoints for version management (Stage 3)."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import get_current_user_id
from backend.db import get_session
from backend.repositories import UserVersionRepository
from backend.schemas import (
    VersionCreateRequest,
    VersionDetailResponse,
    VersionItemResponse,
    VersionListResponse,
)

router = APIRouter(prefix="/versions", tags=["versions"])
logger = logging.getLogger(__name__)


@router.post(
    "",
    response_model=VersionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new version",
)
async def create_version(
    request: VersionCreateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: Annotated[str | None, Depends(get_current_user_id)],
) -> VersionDetailResponse:
    """Save a new version to history."""
    repo = UserVersionRepository(session)

    version = await repo.create(
        user_id=user_id,
        type=request.type,
        title=request.title,
        resume_text=request.resume_text,
        vacancy_text=request.vacancy_text,
        result_text=request.result_text,
        change_log=request.change_log,
        selected_checkbox_ids=request.selected_checkbox_ids,
        analysis_id=request.analysis_id,
    )

    await session.commit()

    return VersionDetailResponse(
        id=str(version.id),
        created_at=version.created_at,
        type=version.type,
        title=version.title,
        resume_text=version.resume_text,
        vacancy_text=version.vacancy_text,
        result_text=version.result_text,
        change_log=version.change_log,
    )


@router.get(
    "",
    response_model=VersionListResponse,
    summary="List all versions",
)
async def list_versions(
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: Annotated[str | None, Depends(get_current_user_id)],
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> VersionListResponse:
    """Get paginated list of versions for the current user."""
    repo = UserVersionRepository(session)
    versions, total = await repo.list_versions(
        limit=limit, offset=offset, user_id=user_id
    )

    return VersionListResponse(
        items=[
            VersionItemResponse(
                id=str(v.id),
                created_at=v.created_at,
                type=v.type,
                title=v.title,
            )
            for v in versions
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{version_id}",
    response_model=VersionDetailResponse,
    summary="Get version by ID",
)
async def get_version(
    version_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: Annotated[str | None, Depends(get_current_user_id)],
) -> VersionDetailResponse:
    """Get full details of a specific version."""
    repo = UserVersionRepository(session)
    version = await repo.get_by_id(version_id, user_id=user_id)

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found",
        )

    return VersionDetailResponse(
        id=str(version.id),
        created_at=version.created_at,
        type=version.type,
        title=version.title,
        resume_text=version.resume_text,
        vacancy_text=version.vacancy_text,
        result_text=version.result_text,
        change_log=version.change_log,
    )


@router.delete(
    "/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete version",
)
async def delete_version(
    version_id: UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    user_id: Annotated[str | None, Depends(get_current_user_id)],
) -> None:
    """Delete a version from history."""
    repo = UserVersionRepository(session)
    deleted = await repo.delete_by_id(version_id, user_id=user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version {version_id} not found",
        )

    await session.commit()
