"""Vacancy domain DTOs."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class VacancyParseResult:
    """Result of vacancy parsing."""

    vacancy_id: UUID
    vacancy_hash: str
    parsed_vacancy: dict[str, Any]
    cache_hit: bool
