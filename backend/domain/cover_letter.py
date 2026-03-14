"""Cover letter domain DTOs."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class CoverLetterResult:
    """Result of cover letter generation."""

    cover_letter_id: UUID
    resume_version_id: UUID
    vacancy_id: UUID | None
    cover_letter_text: str
    structure: dict[str, str]
    key_points_used: list[str]
    alignment_notes: list[str]
    cache_hit: bool
