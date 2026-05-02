"""Match request schemas."""

from typing import Any

from pydantic import BaseModel, Field

from backend.core.config import MAX_RESUME_CHARS, MAX_VACANCY_CHARS


class MatchAnalyzeRequest(BaseModel):
    """Request to analyze resume-vacancy match."""

    resume_text: str = Field(
        ...,
        min_length=10,
        max_length=MAX_RESUME_CHARS,
        description="Raw resume text",
    )
    vacancy_text: str = Field(
        ...,
        min_length=10,
        max_length=MAX_VACANCY_CHARS,
        description="Raw vacancy text",
    )

    # Context for re-analysis after adaptation (optional)
    original_analysis: dict[str, Any] | None = Field(
        default=None,
        description="Original analysis JSON (before adaptation). If provided, enables context-aware re-analysis.",
    )
    applied_checkbox_ids: list[str] | None = Field(
        default=None,
        description="Checkbox IDs that were applied during adaptation. Used with original_analysis.",
    )
