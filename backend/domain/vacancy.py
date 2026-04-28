"""Vacancy domain DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class VacancyParseResult:
    """Result of vacancy parsing."""

    vacancy_id: UUID
    vacancy_hash: str
    parsed_vacancy: dict[str, Any]
    cache_hit: bool


@dataclass
class VacancyDetailResult:
    """Detailed vacancy data for API presentation."""

    id: UUID
    source_text: str
    content_hash: str
    parsed_data: dict[str, Any]
    created_at: datetime
    parsed_at: datetime | None
