"""Full analysis pipeline domain DTOs."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class FullAnalysisResult:
    """Result of full analysis pipeline."""

    resume_id: UUID
    vacancy_id: UUID
    analysis_id: UUID
    parsed_resume: dict[str, Any]
    parsed_vacancy: dict[str, Any]
    analysis: dict[str, Any]
    cache_hit: bool  # True if ALL results were from cache
