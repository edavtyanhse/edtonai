"""Schemas for resume adaptation (adapt_resume operation)."""

from uuid import UUID

from pydantic import BaseModel, Field


class AdaptResumeOptions(BaseModel):
    """Optional settings for resume adaptation."""

    language: str | None = Field(
        default=None,
        description="Target language: ru | en | auto",
    )
    template: str | None = Field(
        default=None,
        description="Resume template style: default | harvard",
    )


class SelectedImprovement(BaseModel):
    """Single improvement selected by user with optional input."""

    checkbox_id: str = Field(..., description="ID of the checkbox/gap")
    user_input: str | None = Field(
        default=None,
        description="User-provided text for this improvement (if requires_user_input)",
    )
    ai_generate: bool = Field(
        default=False,
        description="If true and no user_input, AI will generate minimal generic text",
    )


class AdaptResumeRequest(BaseModel):
    """Request to adapt resume for a vacancy."""

    # Either text or ID must be provided
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

    # New format: list of improvements with optional user input
    selected_improvements: list[SelectedImprovement] = Field(
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


class ChangeLogEntry(BaseModel):
    """Single change made during adaptation."""

    checkbox_id: str = Field(..., description="ID of the checkbox that triggered this change")
    what_changed: str = Field(..., description="Description of what was changed")
    where: str = Field(..., description="Section: summary | skills | experience | education | other")
    before_excerpt: str | None = Field(default=None, description="Original text fragment")
    after_excerpt: str | None = Field(default=None, description="New text fragment")


class AdaptResumeResponse(BaseModel):
    """Response with adapted resume."""

    version_id: UUID = Field(..., description="UUID of the new resume version")
    parent_version_id: UUID | None = Field(
        default=None,
        description="UUID of parent version (null if first adaptation)",
    )
    resume_id: UUID = Field(..., description="UUID of base resume")
    vacancy_id: UUID = Field(..., description="UUID of target vacancy")

    updated_resume_text: str = Field(..., description="Full text of adapted resume")
    change_log: list[ChangeLogEntry] = Field(
        default_factory=list,
        description="List of changes made",
    )
    applied_checkbox_ids: list[str] = Field(
        default_factory=list,
        description="Checkbox IDs that were successfully applied",
    )

    cache_hit: bool = Field(..., description="True if result was from cache")
