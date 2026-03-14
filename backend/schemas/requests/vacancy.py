"""Vacancy request schemas."""

from pydantic import BaseModel, Field


class VacancyParseRequest(BaseModel):
    """Request to parse a vacancy."""

    vacancy_text: str | None = Field(None, description="Raw vacancy text")
    url: str | None = Field(None, description="URL to fetch vacancy from")


class VacancyPatchRequest(BaseModel):
    """Request to update parsed vacancy data."""

    parsed_data: dict = Field(
        ..., description="Updated structured vacancy data (partial or full)"
    )
