"""Resume domain DTOs."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class ResumeParseResult:
    """Result of resume parsing."""

    resume_id: UUID
    resume_hash: str
    parsed_resume: dict[str, Any]
    cache_hit: bool
