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

import contextvars

from dependency_injector import containers, providers

# Per-request session, set by middleware in main.py
request_session: contextvars.ContextVar = contextvars.ContextVar("request_session")
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.auth.oauth_service import OAuthService  # noqa: E402
from backend.auth.service import AuthService  # noqa: E402
from backend.core.config import Settings  # noqa: E402
from backend.integration.ai.base import AIProvider  # noqa: E402
from backend.integration.ai.deepseek import DeepSeekProvider  # noqa: E402
from backend.integration.ai.groq import GroqProvider  # noqa: E402
from backend.integration.email.client import SmtpEmailClient  # noqa: E402
from backend.integration.email.service import EmailService  # noqa: E402
from backend.integration.oauth.base import OAuthProvider  # noqa: E402
from backend.integration.oauth.google import GoogleOAuthProvider  # noqa: E402
from backend.integration.oauth.yandex import YandexOAuthProvider  # noqa: E402
from backend.repositories.ai_result import AIResultRepository  # noqa: E402
from backend.repositories.analysis import AnalysisRepository  # noqa: E402
from backend.repositories.email_verification import (  # noqa: E402
    EmailVerificationRepository,  # noqa: E402
)
from backend.repositories.feedback import FeedbackRepository  # noqa: E402
from backend.repositories.ideal_resume import IdealResumeRepository  # noqa: E402
from backend.repositories.oauth_account import OAuthAccountRepository  # noqa: E402
from backend.repositories.refresh_token_repo import (  # noqa: E402
    RefreshTokenRepository as RefreshTokenRepo,
)
from backend.repositories.resume import ResumeRepository  # noqa: E402
from backend.repositories.resume_version import ResumeVersionRepository  # noqa: E402
from backend.repositories.user import UserRepository  # noqa: E402
from backend.repositories.user_version import UserVersionRepository  # noqa: E402
from backend.repositories.vacancy import VacancyRepository  # noqa: E402
from backend.services.adapt import AdaptResumeService  # noqa: E402
from backend.services.cover_letter import CoverLetterService  # noqa: E402
from backend.services.ideal import IdealResumeService  # noqa: E402
from backend.services.match import MatchService  # noqa: E402
from backend.services.orchestrator import OrchestratorService  # noqa: E402
from backend.services.resume import ResumeService  # noqa: E402
from backend.services.vacancy import VacancyService  # noqa: E402

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


def _create_oauth_providers(settings: Settings) -> dict[str, OAuthProvider]:
    """Build dict of configured OAuth providers. Skips providers without client_id."""
    result: dict[str, OAuthProvider] = {}
    base = settings.backend_url.rstrip("/")

    if settings.google_oauth_client_id:
        result["google"] = GoogleOAuthProvider(
            client_id=settings.google_oauth_client_id,
            client_secret=settings.google_oauth_client_secret,
            redirect_uri=f"{base}/auth/oauth/google/callback",
        )
    if settings.yandex_oauth_client_id:
        result["yandex"] = YandexOAuthProvider(
            client_id=settings.yandex_oauth_client_id,
            client_secret=settings.yandex_oauth_client_secret,
            redirect_uri=f"{base}/auth/oauth/yandex/callback",
        )
    return result


# ── Container ─────────────────────────────────────────────────────


class Container(containers.DeclarativeContainer):
    """Application-level DI container (Composition Root).

    Provider graph::

        Settings (Singleton)
          └─► async_engine (Singleton)
                └─► session_factory (Singleton)
                      └─► session (Dependency, set per-request by middleware)
                            ├─► Repositories (Factory)
                            │     └─► Services (Factory)
                            └─► AI Providers (Factory)
    """

    # Wiring will be done explicitly in main.py
    wiring_config = containers.WiringConfiguration(
        modules=[
            "backend.api.dependencies",
            "backend.auth.router",
            "backend.auth.oauth_router",
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
        pool_pre_ping=True,
        pool_recycle=300,
        connect_args=providers.Dict(statement_cache_size=0),
    )

    session_factory = providers.Singleton(
        async_sessionmaker,
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    session = providers.Callable(lambda: request_session.get())

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

    # ── Auth ───────────────────────────────────────────────────────

    user_repo = providers.Factory(UserRepository, session=session)
    refresh_token_repo = providers.Factory(RefreshTokenRepo, session=session)
    email_verification_repo = providers.Factory(
        EmailVerificationRepository, session=session
    )

    email_client = providers.Singleton(
        SmtpEmailClient,
        host=config.provided.smtp_host,
        port=config.provided.smtp_port,
        username=config.provided.smtp_username,
        password=config.provided.smtp_password,
        from_email=config.provided.smtp_from_email,
    )
    email_service = providers.Factory(EmailService, client=email_client)

    auth_service = providers.Factory(
        AuthService,
        user_repo=user_repo,
        refresh_token_repo=refresh_token_repo,
        email_verification_repo=email_verification_repo,
        email_service=email_service,
        settings=config,
    )

    # ── OAuth ──────────────────────────────────────────────────────

    oauth_account_repo = providers.Factory(OAuthAccountRepository, session=session)

    oauth_providers = providers.Singleton(
        _create_oauth_providers,
        settings=config,
    )

    oauth_service = providers.Factory(
        OAuthService,
        user_repo=user_repo,
        oauth_account_repo=oauth_account_repo,
        refresh_token_repo=refresh_token_repo,
        settings=config,
        providers=oauth_providers,
    )
