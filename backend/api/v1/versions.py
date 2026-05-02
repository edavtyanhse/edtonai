"""API endpoints for version management (Stage 3)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from backend.api.dependencies import get_version_service
from backend.core.auth import require_auth
from backend.schemas import (
    VersionCreateRequest,
    VersionDetailResponse,
    VersionItemResponse,
    VersionListResponse,
)
from backend.services.version import VersionService

router = APIRouter(prefix="/versions", tags=["versions"])


@router.post(
    "",
    response_model=VersionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new version",
)
async def create_version(
    request: VersionCreateRequest,
    user_id: Annotated[str, Depends(require_auth)],
    service: Annotated[VersionService, Depends(get_version_service)],
) -> VersionDetailResponse:
    """Save a new version to history."""
    version = await service.create_version(
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

    return VersionDetailResponse(
        id=version.id,
        created_at=version.created_at,
        type=version.type,
        title=version.title,
        resume_text=version.resume_text,
        vacancy_text=version.vacancy_text,
        result_text=version.result_text,
        change_log=version.change_log,
        selected_checkbox_ids=version.selected_checkbox_ids,
        analysis_id=version.analysis_id,
    )


@router.get(
    "",
    response_model=VersionListResponse,
    summary="List all versions",
)
async def list_versions(
    user_id: Annotated[str, Depends(require_auth)],
    service: Annotated[VersionService, Depends(get_version_service)],
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> VersionListResponse:
    """Get paginated list of versions for the current user."""
    versions = await service.list_versions(
        limit=limit, offset=offset, user_id=user_id
    )

    return VersionListResponse(
        items=[
            VersionItemResponse(
                id=v.id,
                created_at=v.created_at,
                type=v.type,
                title=v.title,
                analysis_id=v.analysis_id,
            )
            for v in versions.items
        ],
        total=versions.total,
        limit=versions.limit,
        offset=versions.offset,
    )


@router.get(
    "/{version_id}",
    response_model=VersionDetailResponse,
    summary="Get version by ID",
)
async def get_version(
    version_id: UUID,
    user_id: Annotated[str, Depends(require_auth)],
    service: Annotated[VersionService, Depends(get_version_service)],
) -> VersionDetailResponse:
    """Get full details of a specific version."""
    version = await service.get_version(version_id, user_id=user_id)

    return VersionDetailResponse(
        id=version.id,
        created_at=version.created_at,
        type=version.type,
        title=version.title,
        resume_text=version.resume_text,
        vacancy_text=version.vacancy_text,
        result_text=version.result_text,
        change_log=version.change_log,
        selected_checkbox_ids=version.selected_checkbox_ids,
        analysis_id=version.analysis_id,
    )


@router.delete(
    "/{version_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete version",
)
async def delete_version(
    version_id: UUID,
    user_id: Annotated[str, Depends(require_auth)],
    service: Annotated[VersionService, Depends(get_version_service)],
) -> None:
    """Delete a version from history."""
    await service.delete_version(version_id, user_id=user_id)
