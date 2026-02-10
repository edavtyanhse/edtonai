"""Vacancy parsing endpoint."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.api.dependencies import get_vacancy_service
from backend.ai.errors import AIError
from backend.db import get_db
from backend.schemas import (
    VacancyParseRequest,
    VacancyParseResponse,
    VacancyPatchRequest,
    VacancyDetailResponse,
)
from backend.services import VacancyService
from backend.repositories import VacancyRepository

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
    if not text and request.url:
        from backend.services.scraper import WebScraper
        try:
            text = await WebScraper.fetch_text(request.url)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=str(e))
            
    if not text or len(text) < 10:
        raise HTTPException(status_code=422, detail="Vacancy text is empty or too short")

    try:
        result = await service.parse_and_cache(text)
    except AIError as e:
        raise HTTPException(status_code=502, detail=f"AI provider error: {e}")

    return VacancyParseResponse(
        vacancy_id=result.vacancy_id,
        vacancy_hash=result.vacancy_hash,
        parsed_vacancy=result.parsed_vacancy,
        cache_hit=result.cache_hit,
    )


@router.get("/{vacancy_id}", response_model=VacancyDetailResponse)
async def get_vacancy(
    vacancy_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> VacancyDetailResponse:
    """Get vacancy by ID with all details."""
    repo = VacancyRepository(db)
    vacancy = await repo.get_by_id(vacancy_id)
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    return VacancyDetailResponse(
        id=vacancy.id,
        source_text=vacancy.source_text,
        content_hash=vacancy.content_hash,
        parsed_data=vacancy.get_parsed_data(),
        created_at=vacancy.created_at,
        parsed_at=vacancy.parsed_at,
    )


@router.patch("/{vacancy_id}", response_model=VacancyDetailResponse)
async def update_vacancy_parsed_data(
    vacancy_id: UUID,
    request: VacancyPatchRequest,
    db: AsyncSession = Depends(get_db),
) -> VacancyDetailResponse:
    """Update parsed data for a vacancy.

    Allows frontend to save edited structured vacancy fields.
    This is separate from the wizard navigation (Next button).
    """
    repo = VacancyRepository(db)
    vacancy = await repo.update_parsed_data(vacancy_id, request.parsed_data)
    if vacancy is None:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    
    await db.commit()
    
    return VacancyDetailResponse(
        id=vacancy.id,
        source_text=vacancy.source_text,
        content_hash=vacancy.content_hash,
        parsed_data=vacancy.get_parsed_data(),
        created_at=vacancy.created_at,
        parsed_at=vacancy.parsed_at,
    )
