# Architecture Overview

Архитектура backend-сервиса построена по принципу многослойности (Layered Architecture) с полноценным DI-контейнером и Protocol-интерфейсами (Dependency Inversion Principle).

## Диаграмма слоёв

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Layer                               │
│                                                                 │
│  api/v1/resumes.py    api/v1/vacancies.py    api/v1/match.py   │
│                                                                 │
│  • FastAPI routers                                              │
│  • Request validation (Pydantic schemas/requests/)              │
│  • Response serialization (Pydantic schemas/responses/)         │
│  • Error handling → global handlers (errors/handlers.py)        │
│  • DI: Depends(get_xxx_service) → @inject из контейнера         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
│                                                                 │
│  services/base.py (CachedAIService)                             │
│  ├── services/resume.py     services/vacancy.py                 │
│  ├── services/match.py      services/orchestrator.py            │
│  ├── services/adapt.py      services/ideal.py                   │
│  └── services/cover_letter.py                                   │
│                                                                 │
│  • Business logic (все наследуют CachedAIService)               │
│  • Caching orchestration (_check_cache / _save_to_cache)        │
│  • AI provider calls (через Protocol AIProvider)                │
│  • Dependencies через Protocol-интерфейсы                       │
│  • Hash computation (utils.py)                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────────┐ ┌─────────────────────────────────────┐
│   Integration Layer     │ │         Repository Layer            │
│                         │ │                                     │
│  integration/ai/        │ │  repositories/interfaces.py         │
│   ├── base.py (ABC)     │ │  repositories/resume.py             │
│   ├── deepseek.py       │ │  repositories/vacancy.py            │
│   ├── groq.py           │ │  repositories/ai_result.py          │
│   └── prompts.py        │ │  repositories/analysis.py           │
│                         │ │  repositories/resume_version.py     │
│  integration/scraper/   │ │  repositories/ideal_resume.py       │
│   └── scraper.py        │ │                                     │
│                         │ │  • CRUD operations                  │
│  • LLM abstraction      │ │  • SQLAlchemy queries               │
│  • HTTP calls           │ │  • Реализуют Protocol-интерфейсы    │
│  • JSON validation      │ │    из repositories/interfaces.py    │
│  • Retry logic          │ │                                     │
│  • Web scraping         │ │                                     │
└─────────────────────────┘ └───────────────────────────┬─────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                │
│                                                                 │
│  models/resume.py    models/vacancy.py    models/ai_result.py   │
│  models/analysis_link.py   models/resume_version.py             │
│  models/ideal_resume.py    models/user_version.py               │
│                                                                 │
│  • SQLAlchemy ORM models (чистые, без бизнес-логики)            │
│  • domain/mappers.py — standalone ORM ↔ dict маппинг            │
│  • PostgreSQL (asyncpg)                                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Error Layer                                │
│                                                                 │
│  errors/base.py       → AppError (базовый класс)                │
│  errors/business.py   → ResumeNotFoundError, VacancyNotFoundError│
│  errors/integration.py → AIProviderError, ScraperError          │
│  errors/handlers.py   → Глобальные FastAPI exception handlers   │
│                                                                 │
│  • Типизированные ошибки с HTTP status codes                    │
│  • Эндпоинты не содержат try/except для бизнес-ошибок           │
│  • handlers.py → автоматическая конвертация в HTTP-ответы       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                   Domain Layer (DTOs)                            │
│                                                                 │
│  domain/resume.py     → ResumeParseResult                       │
│  domain/vacancy.py    → VacancyParseResult                      │
│  domain/match.py      → MatchAnalysisResult                     │
│  domain/adapt.py      → AdaptResumeResult                       │
│  domain/ideal.py      → IdealResumeResult                       │
│  domain/cover_letter.py → CoverLetterResult                     │
│  domain/analysis.py   → FullAnalysisResult                      │
│  domain/mappers.py    → get_/set_parsed_data (ORM ↔ dict)       │
│                                                                 │
│  • Чистые dataclasses — результаты сервисных операций           │
│  • Не привязаны к ORM, API-схемам или AI                        │
└─────────────────────────────────────────────────────────────────┘
```

## Dependency Injection (Composition Root)

```
containers.py (Composition Root)
    │
    ├── Settings (Singleton)
    │
    ├── async_engine (Singleton) ──► database_url из Settings
    │
    ├── session_factory (Singleton) ──► bind к engine
    │
    ├── session (Resource, per-request) ──► commit/rollback/close
    │
    ├── AI Providers (Factory)
    │     ├── ai_provider_parsing ──► Groq (fast)
    │     └── ai_provider_reasoning ──► DeepSeek (smart)
    │
    ├── Repositories (Factory) × 8
    │     ├── resume_repo, vacancy_repo, ai_result_repo
    │     ├── analysis_repo, resume_version_repo
    │     └── ideal_resume_repo, user_version_repo, feedback_repo
    │
    └── Services (Factory) × 7
          ├── resume_service ──► resume_repo + ai_result_repo + ai_provider_parsing
          ├── vacancy_service ──► vacancy_repo + ai_result_repo + ai_provider_parsing
          ├── match_service ──► ai_result_repo + ai_provider_reasoning
          ├── orchestrator_service ──► resume_service + vacancy_service + match_service
          ├── adapt_resume_service ──► все repo + все service + ai_provider_reasoning
          ├── ideal_resume_service ──► vacancy_repo + ideal_repo + vacancy_service
          └── cover_letter_service ──► ai_result_repo + version_repo + vacancy_repo

main.py
    │
    ├── Container() + container.wire() ──► backend.api.dependencies
    │
    └── app = FastAPI(lifespan=...)
          ├── register_exception_handlers(app) ──► errors/handlers.py
          ├── include_router(health_router)
          └── include_router(v1_router)
```

## Принципы

### 1. Dependency Injection через контейнер

Все зависимости собираются в `containers.py` (Composition Root) и инжектируются через `@inject` + `Provide`:

```python
# backend/api/dependencies.py
from dependency_injector.wiring import Provide, inject
from backend.containers import Container

@inject
async def get_resume_service(
    service: ResumeService = Depends(Provide[Container.resume_service]),
) -> ResumeService:
    return service

# backend/api/v1/resumes.py
@router.post("/parse")
async def parse_resume(
    request: ResumeParseRequest,
    service: ResumeService = Depends(get_resume_service),  # ← DI
):
    result = await service.parse_and_cache(request.resume_text)
    ...
```

### 2. Protocol-интерфейсы (Dependency Inversion)

Сервисы зависят от абстракций, а не от конкретных классов:

```python
# repositories/interfaces.py
class IResumeRepository(Protocol):
    async def get_by_hash(self, content_hash: str) -> ResumeRaw | None: ...
    async def create(self, source_text: str, content_hash: str) -> ResumeRaw: ...

# services/resume.py
class ResumeService(CachedAIService):
    def __init__(
        self,
        session: AsyncSession,
        resume_repo: IResumeRepository,   # ← Protocol, не конкретный класс
        ai_result_repo: IAIResultRepository,
        ai_provider: AIProvider,
        settings: Settings,
    ): ...
```

### 3. Repository Pattern

Вся работа с БД изолирована в репозиториях:

```python
class ResumeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_hash(self, content_hash: str) -> ResumeRaw | None:
        stmt = select(ResumeRaw).where(ResumeRaw.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

### 4. CachedAIService (Template Method)

Все AI-сервисы наследуют общий базовый класс, устраняющий дублирование кеширования:

```python
class CachedAIService:
    OPERATION: str  # e.g. "parse_resume"

    def __init__(self, session, ai_provider, settings, ai_result_repo=None): ...

    async def _check_cache(self, input_hash: str) -> AIResult | None
    async def _save_to_cache(self, input_hash: str, output_json: dict) -> AIResult
    async def _call_ai_with_cache(self, input_hash, prompt) -> (dict, bool)
    def _post_process_output(self, output_json) -> dict  # hook
    provider_name: str  # property
    model_name: str     # property
```

### 5. AI Abstraction

AI-провайдеры абстрагированы через ABC для горячей замены Groq ↔ DeepSeek:

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str, prompt_name: str) -> dict:
        pass

# Конкретные провайдеры:
class DeepSeekProvider(AIProvider): ...  # reasoning tasks
class GroqProvider(AIProvider): ...      # parsing tasks
```

Выбор провайдера — в контейнере через `ai_provider_parsing` / `ai_provider_reasoning`.

### 6. Error Taxonomy

Типизированные ошибки обрабатываются глобально:

```python
# errors/base.py
class AppError(Exception):
    status_code: int = 500
    message: str

# errors/business.py
class ResumeNotFoundError(AppError):
    status_code = 404

# errors/handlers.py — регистрация в main.py
@app.exception_handler(AppError)
async def app_error_handler(request, exc):
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})
```

Эндпоинты **не** содержат `try/except` для бизнес-ошибок — всё перехватывается автоматически.

## Файлы по слоям

| Layer | Files | Responsibility |
|-------|-------|----------------|
| HTTP | `api/v1/*.py` | Роуты, валидация, HTTP |
| DI | `containers.py`, `api/dependencies.py` | Composition Root, wiring |
| Service | `services/*.py` | Бизнес-логика |
| Repository | `repositories/*.py` | CRUD, SQL |
| Model | `models/*.py` | ORM сущности (чистые) |
| Domain | `domain/*.py` | DTO dataclasses, маппинг |
| Integration | `integration/ai/*.py`, `integration/scraper/*.py` | LLM, scraping |
| Error | `errors/*.py` | Таксономия ошибок, handlers |
| Schema | `schemas/requests/*.py`, `schemas/responses/*.py`, `schemas/common.py` | Pydantic request/response |
| Core | `core/*.py` | Конфиг, логирование, auth |
| DB | `db/*.py` | Сессии, base model |

## Тестирование

```
tests/
├── conftest.py         # container.override() + test DB fixtures
├── unit/
│   ├── test_services.py    # Мок-зависимости, Protocol-based
│   └── test_container.py   # Smoke-тесты контейнера
└── integration/
    ├── test_health.py      # Health endpoint
    ├── test_api_validation.py  # Pydantic validation
    └── test_business_flow.py   # Full flow с тестовой БД
```

Тесты используют `container.override()` — **без** `unittest.mock.patch` на пути импорта.
