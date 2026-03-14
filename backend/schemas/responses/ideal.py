"""Ideal resume response schemas."""

from uuid import UUID

from pydantic import BaseModel, Field

from backend.schemas.common import IdealResumeMetadata


class IdealResumeResponse(BaseModel):
    """Response with generated ideal resume."""

    ideal_id: UUID = Field(..., description="UUID of the ideal resume record")
    vacancy_id: UUID = Field(..., description="UUID of the target vacancy")

    ideal_resume_text: str = Field(..., description="Full text of the ideal resume")
    metadata: IdealResumeMetadata = Field(
        default_factory=IdealResumeMetadata,
        description="Generation metadata",
    )

    cache_hit: bool = Field(..., description="True if result was from cache")
