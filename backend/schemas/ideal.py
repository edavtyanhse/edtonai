"""Schemas for ideal resume generation (ideal_resume operation)."""

from uuid import UUID

from pydantic import BaseModel, Field


class IdealResumeOptions(BaseModel):
    """Options for ideal resume generation."""

    language: str | None = Field(
        default=None,
        description="Target language: ru | en | auto",
    )
    template: str | None = Field(
        default=None,
        description="Resume template style: default | harvard",
    )
    seniority: str | None = Field(
        default=None,
        description="Target seniority level: junior | middle | senior | any",
    )


class IdealResumeRequest(BaseModel):
    """Request to generate ideal resume for a vacancy."""

    # Either text or ID must be provided
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


class IdealResumeMetadata(BaseModel):
    """Metadata about the generated ideal resume."""

    keywords_used: list[str] = Field(
        default_factory=list,
        description="ATS keywords included in the resume",
    )
    structure: list[str] = Field(
        default_factory=list,
        description="Sections used in the resume",
    )
    assumptions: list[str] = Field(
        default_factory=list,
        description="Assumptions made during generation",
    )
    language: str | None = Field(
        default=None,
        description="Language of the generated resume",
    )
    template: str | None = Field(
        default=None,
        description="Template style used",
    )


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
