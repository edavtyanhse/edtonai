"""Adapt resume response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.common import ChangeLogEntry


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
