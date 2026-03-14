"""Adapt resume request schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.common import AdaptResumeOptions, SelectedImprovementSchema


class AdaptResumeRequest(BaseModel):
    """Request to adapt resume for a vacancy."""

    resume_text: str | None = Field(
        default=None,
        min_length=10,
        description="Raw resume text (if not using resume_id)",
    )
    resume_id: UUID | None = Field(
        default=None,
        description="UUID of existing resume (if already parsed)",
    )

    vacancy_text: str | None = Field(
        default=None,
        min_length=10,
        description="Raw vacancy text (if not using vacancy_id)",
    )
    vacancy_id: UUID | None = Field(
        default=None,
        description="UUID of existing vacancy (if already parsed)",
    )

    selected_improvements: list[SelectedImprovementSchema] = Field(
        default_factory=list,
        description="List of improvements with optional user input",
    )

    # Legacy format for backward compatibility
    selected_checkbox_ids: list[str] | None = Field(
        default=None,
        description="DEPRECATED: Use selected_improvements instead. List of checkbox IDs.",
    )

    base_version_id: UUID | None = Field(
        default=None,
        description="UUID of parent version (if adapting from existing version)",
    )

    options: AdaptResumeOptions = Field(
        default_factory=AdaptResumeOptions,
        description="Optional adaptation settings",
    )
