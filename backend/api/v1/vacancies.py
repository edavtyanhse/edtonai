"""Vacancy parsing endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_vacancy_service
from backend.schemas import (
    VacancyDetailResponse,
    VacancyParseRequest,
    VacancyParseResponse,
    VacancyPatchRequest,
)
from backend.services import VacancyService

router = APIRouter(prefix="/vacancies", tags=["vacancies"])


@router.post("/parse", response_model=VacancyParseResponse)
async def parse_vacancy(
    request: VacancyParseRequest,
    service: VacancyService = Depends(get_vacancy_service),
) -> VacancyParseResponse:
    """Parse vacancy text and return structured data.

    - Caches results by content hash
    - Returns cache_hit=true if result was from cache
    """
    text = request.vacancy_text
    source_url = request.url
    if not text and source_url:
        from backend.integration.scraper import WebScraper

        text = await WebScraper.fetch_text(source_url)

    if not text or len(text) < 10:
        raise HTTPException(
            status_code=422, detail="Vacancy text is empty or too short"
        )

    result = await service.parse_and_cache(text, source_url=source_url)

    return VacancyParseResponse(
        vacancy_id=result.vacancy_id,
        vacancy_hash=result.vacancy_hash,
        parsed_vacancy=result.parsed_vacancy,
        cache_hit=result.cache_hit,
        raw_text=text,
    )


@router.get("/{vacancy_id}", response_model=VacancyDetailResponse)
async def get_vacancy(
    vacancy_id: UUID,
    service: VacancyService = Depends(get_vacancy_service),
) -> VacancyDetailResponse:
    """Get vacancy by ID with all details."""
    vacancy = await service.get_detail(vacancy_id)

    return VacancyDetailResponse(
        id=vacancy.id,
        source_text=vacancy.source_text,
        content_hash=vacancy.content_hash,
        parsed_data=vacancy.parsed_data,
        created_at=vacancy.created_at,
        parsed_at=vacancy.parsed_at,
    )


@router.patch("/{vacancy_id}", response_model=VacancyDetailResponse)
async def update_vacancy_parsed_data(
    vacancy_id: UUID,
    request: VacancyPatchRequest,
    service: VacancyService = Depends(get_vacancy_service),
) -> VacancyDetailResponse:
    """Update parsed data for a vacancy.

    Allows frontend to save edited structured vacancy fields.
    This is separate from the wizard navigation (Next button).
    """
    vacancy = await service.update_parsed_data(vacancy_id, request.parsed_data)

    return VacancyDetailResponse(
        id=vacancy.id,
        source_text=vacancy.source_text,
        content_hash=vacancy.content_hash,
        parsed_data=vacancy.parsed_data,
        created_at=vacancy.created_at,
        parsed_at=vacancy.parsed_at,
    )
