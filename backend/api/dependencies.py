"""API-level dependency providers for services.

Uses dependency-injector: each ``get_xxx_service()`` callable resolves
a fully-assembled service from the application DI container.

Routes keep the familiar ``Depends(get_xxx_service)`` pattern.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from backend.containers import Container
from backend.services.adapt import AdaptResumeService
from backend.services.cover_letter import CoverLetterService
from backend.services.ideal import IdealResumeService
from backend.services.orchestrator import OrchestratorService
from backend.services.resume import ResumeService
from backend.services.vacancy import VacancyService


@inject
async def get_resume_service(
    service: ResumeService = Depends(Provide[Container.resume_service]),
) -> ResumeService:
    """Provide ResumeService assembled by DI container."""
    return service


@inject
async def get_vacancy_service(
    service: VacancyService = Depends(Provide[Container.vacancy_service]),
) -> VacancyService:
    """Provide VacancyService assembled by DI container."""
    return service


@inject
async def get_orchestrator_service(
    service: OrchestratorService = Depends(Provide[Container.orchestrator_service]),
) -> OrchestratorService:
    """Provide OrchestratorService assembled by DI container."""
    return service


@inject
async def get_adapt_resume_service(
    service: AdaptResumeService = Depends(Provide[Container.adapt_resume_service]),
) -> AdaptResumeService:
    """Provide AdaptResumeService assembled by DI container."""
    return service


@inject
async def get_ideal_resume_service(
    service: IdealResumeService = Depends(Provide[Container.ideal_resume_service]),
) -> IdealResumeService:
    """Provide IdealResumeService assembled by DI container."""
    return service


@inject
async def get_cover_letter_service(
    service: CoverLetterService = Depends(Provide[Container.cover_letter_service]),
) -> CoverLetterService:
    """Provide CoverLetterService assembled by DI container."""
    return service
