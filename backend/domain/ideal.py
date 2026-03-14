"""Ideal resume domain DTOs."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class IdealResumeResult:
    """Result of ideal resume generation."""

    ideal_id: UUID
    vacancy_id: UUID
    ideal_resume_text: str
    metadata: dict[str, Any]
    cache_hit: bool
