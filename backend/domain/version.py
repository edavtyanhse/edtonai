"""Version domain DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class VersionItemResult:
    """Summary item for version lists."""

    id: str
    created_at: datetime
    type: str
    title: str | None
    analysis_id: str | None


@dataclass
class VersionDetailResult:
    """Detailed version data."""

    id: str
    created_at: datetime
    type: str
    title: str | None
    resume_text: str
    vacancy_text: str
    result_text: str
    change_log: list[dict[str, Any]]
    selected_checkbox_ids: list[str]
    analysis_id: str | None


@dataclass
class VersionListResult:
    """Paginated version list."""

    items: list[VersionItemResult]
    total: int
    limit: int
    offset: int
