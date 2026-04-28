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
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from backend.auth.oauth_service import OAuthService
from backend.auth.service import AuthService
from backend.core.config import Settings
from backend.integration.ai.base import AIProvider
from backend.integration.ai.deepseek import DeepSeekProvider
from backend.integration.ai.fallback import FallbackProvider
from backend.integration.ai.groq import GroqProvider
from backend.integration.ai.huggingface import HuggingFaceProvider
from backend.integration.ai.local_hf import LocalHFProvider
from backend.integration.ai.scorer import ResumeScorer
from backend.integration.email.client import SmtpEmailClient
from backend.integration.email.service import EmailService
from backend.integration.oauth.base import OAuthProvider
from backend.integration.oauth.google import GoogleOAuthProvider
from backend.integration.oauth.yandex import YandexOAuthProvider
from backend.repositories.ai_result import AIResultRepository
from backend.repositories.analysis import AnalysisRepository
from backend.repositories.email_verification import (
    EmailVerificationRepository,
)
from backend.repositories.feedback import FeedbackRepository
from backend.repositories.ideal_resume import IdealResumeRepository
from backend.repositories.oauth_account import OAuthAccountRepository
from backend.repositories.refresh_token_repo import (
    RefreshTokenRepository as RefreshTokenRepo,
)
from backend.repositories.resume import ResumeRepository
from backend.repositories.resume_version import ResumeVersionRepository
from backend.repositories.user import UserRepository
from backend.repositories.user_version import UserVersionRepository
from backend.repositories.vacancy import VacancyRepository
from backend.services.adapt import AdaptResumeService
from backend.services.analytics import AnalyticsService
from backend.services.cover_letter import CoverLetterService
from backend.services.feedback import FeedbackService
from backend.services.ideal import IdealResumeService
from backend.services.match import MatchService
from backend.services.orchestrator import OrchestratorService
from backend.services.resume import ResumeService
from backend.services.vacancy import VacancyService
from backend.services.version import VersionService

# Per-request session, set by middleware in main.py
request_session: contextvars.ContextVar = contextvars.ContextVar("request_session")

# ── Helpers ───────────────────────────────────────────────────────


def _create_ai_provider(settings: Settings, task_type: str) -> AIProvider:
    """Factory function: choose AI provider based on settings + task type.

    For reasoning tasks: if hf_endpoint_url is set, use HF generator as primary
    with DeepSeek as automatic fallback. Otherwise use configured provider directly.
    """
    if task_type == "parsing":
        provider_name = settings.ai_provider_parsing.lower()
        groq_model = settings.groq_model_parsing
    else:
        provider_name = settings.ai_provider_reasoning.lower()
        groq_model = settings.groq_model_reasoning

    if provider_name == "groq":
        return GroqProvider(
            api_key=settings.groq_api_key,
            model=groq_model,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
        )
    if provider_name == "deepseek":
        # If HF endpoint is configured — use generator as primary, DeepSeek as fallback
        if task_type == "reasoning" and settings.hf_endpoint_url:
            hf = HuggingFaceProvider(
                model="edmon03/edtonai-generator",
                api_key=settings.hf_token,
                endpoint_url=settings.hf_endpoint_url,
                temperature=settings.ai_temperature,
                max_tokens=settings.ai_max_tokens,
                max_retries=1,
                timeout_seconds=settings.ai_timeout_seconds,
            )
            return FallbackProvider(
                primary=hf,
                fallback=_create_deepseek_provider(settings),
            )
        return _create_deepseek_provider(settings)
    if provider_name == "huggingface":
        return HuggingFaceProvider(
            model=settings.hf_model_reasoning,
            api_key=settings.hf_token,
            endpoint_url=settings.hf_endpoint_url,
            temperature=settings.ai_temperature,
            max_tokens=settings.ai_max_tokens,
            max_retries=settings.ai_max_retries,
            timeout_seconds=settings.ai_timeout_seconds,
        )
    if provider_name == "local_hf":
        return LocalHFProvider(
            model_id=settings.hf_model_reasoning,
            temperature=settings.ai_temperature,
        )
    raise ValueError(f"Unsupported AI provider: {provider_name}")


def _create_deepseek_provider(settings: Settings) -> DeepSeekProvider:
    """Create DeepSeek provider from explicit settings."""
    return DeepSeekProvider(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
        model=settings.ai_model,
        timeout_seconds=settings.ai_timeout_seconds,
        max_retries=settings.ai_max_retries,
        temperature=settings.ai_temperature,
        max_tokens=settings.ai_max_tokens,
    )


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

    # ── Semantic Scorer ───────────────────────────────────────────

    resume_scorer = providers.Singleton(
        ResumeScorer,
        model_path=config.provided.scorer_model_path,
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
        scorer=resume_scorer,
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

    version_service = providers.Factory(
        VersionService,
        user_version_repo=user_version_repo,
    )

    feedback_service = providers.Factory(
        FeedbackService,
        feedback_repo=feedback_repo,
        settings=config,
    )

    analytics_service = providers.Factory(AnalyticsService)

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
