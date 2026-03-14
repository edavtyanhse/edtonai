"""Version response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class VersionItemResponse(BaseModel):
    """Summary item for version list."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    type: str
    title: str | None = None


class VersionDetailResponse(BaseModel):
    """Full version details."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    created_at: datetime
    type: str
    title: str | None = None
    resume_text: str
    vacancy_text: str
    result_text: str
    change_log: list[dict[str, Any]] = []


class VersionListResponse(BaseModel):
    """Paginated list of versions."""

    items: list[VersionItemResponse]
    total: int
    limit: int
    offset: int
