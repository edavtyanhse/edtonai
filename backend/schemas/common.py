"""Common schemas shared between requests and responses."""

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


class ChangeLogEntry(BaseModel):
    """Single change made during adaptation."""

    checkbox_id: str = Field(..., description="ID of the checkbox that triggered this change")
    what_changed: str = Field(..., description="Description of what was changed")
    where: str = Field(..., description="Section: summary | skills | experience | education | other")
    before_excerpt: str | None = Field(default=None, description="Original text fragment")
    after_excerpt: str | None = Field(default=None, description="New text fragment")


class CoverLetterStructure(BaseModel):
    """Structure breakdown of the cover letter."""

    opening: str = Field(..., description="Opening paragraph")
    body: str = Field(..., description="Main argumentation")
    closing: str = Field(..., description="Closing paragraph")


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


class SelectedImprovementSchema(BaseModel):
    """Single improvement selected by user with optional input (API schema)."""

    checkbox_id: str = Field(..., description="ID of the checkbox/gap")
    user_input: str | None = Field(
        default=None,
        description="User-provided text for this improvement (if requires_user_input)",
    )
    ai_generate: bool = Field(
        default=False,
        description="If true and no user_input, AI will generate minimal generic text",
    )
