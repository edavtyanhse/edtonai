# Architecture Overview

Архитектура backend-сервиса построена по принципу многослойности (Layered Architecture).

## Диаграмма слоёв

```
┌─────────────────────────────────────────────────────────────────┐
│                        HTTP Layer                               │
│                                                                 │
│  api/v1/resumes.py    api/v1/vacancies.py    api/v1/match.py   │
│                                                                 │
│  • FastAPI routers                                              │
│  • Request validation (Pydantic)                                │
│  • Response serialization                                       │
│  • Error handling → HTTP codes                                  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Service Layer                              │
│                                                                 │
│  services/resume.py    services/vacancy.py    services/match.py │
│                      services/orchestrator.py                   │
│                                                                 │
│  • Business logic                                               │
│  • Caching orchestration                                        │
│  • AI provider calls                                            │
│  • Hash computation                                             │
└───────────────────────────┬─────────────────────────────────────┘
                            │
              ┌─────────────┴─────────────┐
              │                           │
              ▼                           ▼
┌─────────────────────────┐ ┌─────────────────────────────────────┐
│      AI Layer           │ │         Repository Layer            │
│                         │ │                                     │
│  ai/base.py             │ │  repositories/resume.py             │
│  ai/deepseek.py         │ │  repositories/vacancy.py            │
│                         │ │  repositories/ai_result.py          │
│  • LLM abstraction      │ │  repositories/analysis.py           │
│  • HTTP calls           │ │                                     │
│  • JSON validation      │ │  • CRUD operations                  │
│  • Retry logic          │ │  • SQLAlchemy queries               │
└─────────────────────────┘ └───────────────────────────┬─────────┘
                                                        │
                                                        ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Data Layer                                │
│                                                                 │
│  models/resume.py    models/vacancy.py    models/ai_result.py   │
│                      models/analysis_link.py                    │
│                                                                 │
│  • SQLAlchemy ORM models                                        │
│  • PostgreSQL (asyncpg)                                         │
└─────────────────────────────────────────────────────────────────┘
```

## Dependency Flow

```
main.py
    │
    ├── api/v1/
    │       │
    │       ├── api/dependencies.py ──────► Services factories
    │       │                                   │
    │       │                                   ├── Depends(get_db) ──► db/session.py
    │       │                                   │
    │       │                                   └── Return Service instances
    │       │
    │       └── Endpoints ────────────────► Depends(get_*_service)
    │                                           │
    │                                           └── Services ─────► services/
    │                                                                   │
    │                                                                   ├── Repositories ──► repositories/
    │                                                                   │                         │
    │                                                                   │                         └── Models ──► models/
    │                                                                   │
    │                                                                   └── AI Provider ──► ai/deepseek.py
    │                                                                               │
    │                                                                               └── Settings ──► core/config.py
    │
    └── core/
            ├── config.py (Settings)
            └── logging.py
```

## Принципы

### 1. Dependency Injection

Зависимости инжектируются через FastAPI `Depends()` и централизованы в `api/dependencies.py`:

```python
# api/dependencies.py
def get_resume_service(
    db: AsyncSession = Depends(get_db),
) -> ResumeService:
    return ResumeService(db)

# api/v1/resumes.py
@router.post("/parse")
async def parse_resume(
    request: ResumeParseRequest,
    service: ResumeService = Depends(get_resume_service),  # ← DI
):
    result = await service.parse_and_cache(request.resume_text)
    ...
```

### 2. Repository Pattern

Вся работа с БД изолирована в репозиториях:

```python
class ResumeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_hash(self, content_hash: str) -> Optional[ResumeRaw]:
        stmt = select(ResumeRaw).where(ResumeRaw.content_hash == content_hash)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
```

### 3. Service Layer

Бизнес-логика в сервисах, не в роутерах:

```python
class ResumeService:
    def __init__(self, session: AsyncSession):
        self.resume_repo = ResumeRepository(session)
        self.ai_result_repo = AIResultRepository(session)
        self.ai_provider = DeepSeekProvider()
    
    async def parse_and_cache(self, resume_text: str) -> ResumeParseResult:
        # Business logic here
        ...
```

### 4. AI Abstraction

AI-провайдер абстрагирован интерфейсом для возможной замены:

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate_json(self, prompt: str, prompt_name: str) -> dict:
        pass

class DeepSeekProvider(AIProvider):
    async def generate_json(self, prompt: str, prompt_name: str) -> dict:
        # DeepSeek implementation
        ...
```

## Файлы

| Layer | Files | Responsibility |
|-------|-------|----------------|
| HTTP | `api/v1/*.py` | Роуты, валидация, HTTP |
| Service | `services/*.py` | Бизнес-логика |
| Repository | `repositories/*.py` | CRUD, SQL |
| Model | `models/*.py` | ORM сущности |
| AI | `ai/*.py` | LLM интеграция |
| Schema | `schemas/*.py` | Pydantic request/response |
| Core | `core/*.py` | Конфиг, логирование |
| DB | `db/*.py` | Сессии, base model |
