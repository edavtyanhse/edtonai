"""Match analysis domain DTOs."""

from dataclasses import dataclass
from typing import Any
from uuid import UUID


@dataclass
class MatchAnalysisResult:
    """Result of match analysis."""

    analysis_id: UUID
    analysis: dict[str, Any]
    cache_hit: bool
