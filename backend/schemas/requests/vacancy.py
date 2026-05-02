"""Vacancy request schemas."""

from pydantic import BaseModel, Field

from backend.core.config import MAX_VACANCY_CHARS


class VacancyParseRequest(BaseModel):
    """Request to parse a vacancy."""

    vacancy_text: str | None = Field(
        None,
        min_length=10,
        max_length=MAX_VACANCY_CHARS,
        description="Raw vacancy text",
    )
    url: str | None = Field(None, max_length=2048, description="URL to fetch vacancy from")


class VacancyPatchRequest(BaseModel):
    """Request to update parsed vacancy data."""

    parsed_data: dict = Field(
        ..., description="Updated structured vacancy data (partial or full)"
    )
