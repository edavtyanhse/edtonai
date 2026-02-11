"""API-level dependency providers for services."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db import get_db
from backend.services import (
    AdaptResumeService,
    CoverLetterService,
    IdealResumeService,
    OrchestratorService,
    ResumeService,
    VacancyService,
)


def get_resume_service(
    db: AsyncSession = Depends(get_db),
) -> ResumeService:
    """Provide ResumeService bound to the request DB session."""
    return ResumeService(db)


def get_vacancy_service(
    db: AsyncSession = Depends(get_db),
) -> VacancyService:
    """Provide VacancyService bound to the request DB session."""
    return VacancyService(db)


def get_orchestrator_service(
    db: AsyncSession = Depends(get_db),
) -> OrchestratorService:
    """Provide OrchestratorService bound to the request DB session."""
    return OrchestratorService(db)


def get_adapt_resume_service(
    db: AsyncSession = Depends(get_db),
) -> AdaptResumeService:
    """Provide AdaptResumeService bound to the request DB session."""
    return AdaptResumeService(db)


def get_ideal_resume_service(
    db: AsyncSession = Depends(get_db),
) -> IdealResumeService:
    """Provide IdealResumeService bound to the request DB session."""
    return IdealResumeService(db)


def get_cover_letter_service(
    db: AsyncSession = Depends(get_db),
) -> CoverLetterService:
    """Provide CoverLetterService bound to the request DB session."""
    return CoverLetterService(db)
