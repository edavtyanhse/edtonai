"""Adapt resume domain DTOs."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class SelectedImprovement:
    """Single improvement with optional user input."""

    checkbox_id: str
    user_input: str | None = None
    ai_generate: bool = False


@dataclass
class AdaptResumeResult:
    """Result of resume adaptation."""

    version_id: UUID
    parent_version_id: UUID | None
    resume_id: UUID
    vacancy_id: UUID
    updated_resume_text: str
    change_log: list[dict[str, Any]]
    applied_checkbox_ids: list[str]
    cache_hit: bool
