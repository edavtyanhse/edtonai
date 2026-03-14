"""Ideal resume request schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.common import IdealResumeOptions


class IdealResumeRequest(BaseModel):
    """Request to generate ideal resume for a vacancy."""

    vacancy_text: str | None = Field(
        default=None,
        min_length=10,
        description="Raw vacancy text (if not using vacancy_id)",
    )
    vacancy_id: UUID | None = Field(
        default=None,
        description="UUID of existing vacancy (if already parsed)",
    )

    options: IdealResumeOptions = Field(
        default_factory=IdealResumeOptions,
        description="Generation options",
    )
