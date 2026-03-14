"""Composition Root — единый DI-контейнер приложения.

Все зависимости (settings, DB-сессия, AI-провайдеры, репозитории, сервисы)
собираются здесь. Модули API получают готовые сервисы через ``@inject``.

Пример использования в тестах::

    container = Container()
    container.config.from_dict({...})
    with container.resume_service.override(mock_service):
        ...
"""

from __future__ import annotations

from collections.abc import AsyncGenerator

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import Settings
from backend.integration.ai.base import AIProvider
from backend.integration.ai.deepseek import DeepSeekProvider
from backend.integration.ai.groq import GroqProvider
from backend.repositories.ai_result import AIResultRepository
from backend.repositories.analysis import AnalysisRepository
from backend.repositories.feedback import FeedbackRepository
from backend.repositories.ideal_resume import IdealResumeRepository
from backend.repositories.resume import ResumeRepository
from backend.repositories.resume_version import ResumeVersionRepository
from backend.repositories.user_version import UserVersionRepository
from backend.repositories.vacancy import VacancyRepository
from backend.services.adapt import AdaptResumeService
from backend.services.cover_letter import CoverLetterService
from backend.services.ideal import IdealResumeService
from backend.services.match import MatchService
from backend.services.orchestrator import OrchestratorService
from backend.services.resume import ResumeService
from backend.services.vacancy import VacancyService

# ── Helpers ───────────────────────────────────────────────────────


def _create_ai_provider(settings: Settings, task_type: str) -> AIProvider:
    """Factory function: choose AI provider based on settings + task type."""
    if task_type == "parsing":
        provider_name = settings.ai_provider_parsing.lower()
        groq_model = settings.groq_model_parsing
    else:
        provider_name = settings.ai_provider_reasoning.lower()
        groq_model = settings.groq_model_reasoning

    if provider_name == "groq":
        return GroqProvider(model=groq_model)
    if provider_name == "deepseek":
        return DeepSeekProvider()
    raise ValueError(f"Unsupported AI provider: {provider_name}")


async def _async_session_resource(
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    """Resource provider: open session → yield → commit/rollback → close."""
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# ── Container ─────────────────────────────────────────────────────


class Container(containers.DeclarativeContainer):
    """Application-level DI container (Composition Root).

    Provider graph::

        Settings (Singleton)
          └─► async_engine (Singleton)
                └─► session_factory (Singleton)
                      └─► session (Resource, per-request)
                            ├─► Repositories (Factory)
                            │     └─► Services (Factory)
                            └─► AI Providers (Factory)
    """

    # Wiring will be done explicitly in main.py
    wiring_config = containers.WiringConfiguration(
        modules=[
            "backend.api.dependencies",
        ],
    )

    # ── Configuration ─────────────────────────────────────────────

    config = providers.Singleton(Settings)

    # ── Database ──────────────────────────────────────────────────

    async_engine = providers.Singleton(
        create_async_engine,
        url=config.provided.database_url,
        echo=False,
        future=True,
        connect_args=providers.Dict(statement_cache_size=0),
    )

    session_factory = providers.Singleton(
        async_sessionmaker,
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    session = providers.Resource(
        _async_session_resource,
        session_factory=session_factory,
    )

    # ── AI Providers ──────────────────────────────────────────────

    ai_provider_parsing = providers.Factory(
        _create_ai_provider,
        settings=config,
        task_type="parsing",
    )

    ai_provider_reasoning = providers.Factory(
        _create_ai_provider,
        settings=config,
        task_type="reasoning",
    )

    # ── Repositories ──────────────────────────────────────────────

    resume_repo = providers.Factory(ResumeRepository, session=session)
    vacancy_repo = providers.Factory(VacancyRepository, session=session)
    ai_result_repo = providers.Factory(AIResultRepository, session=session)
    analysis_repo = providers.Factory(AnalysisRepository, session=session)
    resume_version_repo = providers.Factory(ResumeVersionRepository, session=session)
    ideal_resume_repo = providers.Factory(IdealResumeRepository, session=session)
    user_version_repo = providers.Factory(UserVersionRepository, session=session)
    feedback_repo = providers.Factory(FeedbackRepository, session=session)

    # ── Services ──────────────────────────────────────────────────

    resume_service = providers.Factory(
        ResumeService,
        session=session,
        resume_repo=resume_repo,
        ai_result_repo=ai_result_repo,
        ai_provider=ai_provider_parsing,
        settings=config,
    )

    vacancy_service = providers.Factory(
        VacancyService,
        session=session,
        vacancy_repo=vacancy_repo,
        ai_result_repo=ai_result_repo,
        ai_provider=ai_provider_parsing,
        settings=config,
    )

    match_service = providers.Factory(
        MatchService,
        session=session,
        ai_result_repo=ai_result_repo,
        ai_provider=ai_provider_reasoning,
        settings=config,
    )

    orchestrator_service = providers.Factory(
        OrchestratorService,
        session=session,
        resume_service=resume_service,
        vacancy_service=vacancy_service,
        match_service=match_service,
        analysis_repo=analysis_repo,
    )

    adapt_resume_service = providers.Factory(
        AdaptResumeService,
        session=session,
        resume_repo=resume_repo,
        vacancy_repo=vacancy_repo,
        ai_result_repo=ai_result_repo,
        version_repo=resume_version_repo,
        resume_service=resume_service,
        vacancy_service=vacancy_service,
        match_service=match_service,
        ai_provider=ai_provider_reasoning,
        settings=config,
    )

    ideal_resume_service = providers.Factory(
        IdealResumeService,
        session=session,
        vacancy_repo=vacancy_repo,
        ideal_repo=ideal_resume_repo,
        vacancy_service=vacancy_service,
        ai_provider=ai_provider_reasoning,
        settings=config,
    )

    cover_letter_service = providers.Factory(
        CoverLetterService,
        session=session,
        ai_result_repo=ai_result_repo,
        version_repo=resume_version_repo,
        user_version_repo=user_version_repo,
        vacancy_repo=vacancy_repo,
        ai_provider=ai_provider_reasoning,
        settings=config,
    )
