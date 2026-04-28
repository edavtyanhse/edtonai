"""Resume domain DTOs."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID


@dataclass
class ResumeParseResult:
    """Result of resume parsing."""

    resume_id: UUID
    resume_hash: str
    parsed_resume: dict[str, Any]
    cache_hit: bool


@dataclass
class ResumeDetailResult:
    """Detailed resume data for API presentation."""

    id: UUID
    source_text: str
    content_hash: str
    parsed_data: dict[str, Any]
    created_at: datetime
    parsed_at: datetime | None
