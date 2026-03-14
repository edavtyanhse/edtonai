# Services Layer

Сервисный слой содержит бизнес-логику приложения.

## Архитектура

### CachedAIService (базовый класс)

Все AI-сервисы наследуют `CachedAIService` (`backend/services/base.py`), который устраняет дублирование кеширования:

```python
class CachedAIService:
    OPERATION: str  # "parse_resume", "analyze_match", ...

    def __init__(
        self,
        session: AsyncSession,
        ai_provider: AIProvider,       # ABC — через DI
        settings: Settings,            # через DI
        ai_result_repo: IAIResultRepository | None = None,  # Protocol
    ): ...

    # Общие методы:
    async def _check_cache(input_hash) -> AIResult | None
    async def _save_to_cache(input_hash, output_json) -> AIResult
    async def _call_ai_with_cache(input_hash, prompt) -> (dict, bool)
    def _post_process_output(output_json) -> dict  # hook для переопределения

    # Properties:
    provider_name: str   # e.g. "groq", "deepseek"
    model_name: str      # e.g. "llama-3.1-8b-instant"
```

### Dependency Injection

Все зависимости инжектируются через конструктор. Сервисы **никогда** не создают зависимости сами — это делает DI-контейнер (`containers.py`):

```python
# containers.py
resume_service = Factory(
    ResumeService,
    session=session,
    resume_repo=resume_repo,           # IResumeRepository
    ai_result_repo=ai_result_repo,     # IAIResultRepository
    ai_provider=ai_provider_parsing,   # AIProvider (Groq)
    settings=config,                   # Settings
)
```

### Protocol-интерфейсы

Зависимости типизированы через `Protocol` (`services/interfaces.py`, `repositories/interfaces.py`):

```python
# services/interfaces.py
class IResumeService(Protocol):
    async def parse_and_cache(self, resume_text: str) -> ResumeParseResult: ...

# repositories/interfaces.py
class IResumeRepository(Protocol):
    async def get_by_hash(self, content_hash: str) -> ResumeRaw | None: ...
    async def create(self, source_text: str, content_hash: str) -> ResumeRaw: ...
```

## Обзор сервисов

### Парсинг и анализ

| Service | File | AI Provider | Responsibility |
|---------|------|-------------|----------------|
| `ResumeService` | `services/resume.py` | Parsing (Groq) | Парсинг и кеширование резюме |
| `VacancyService` | `services/vacancy.py` | Parsing (Groq) | Парсинг и кеширование вакансий |
| `MatchService` | `services/match.py` | Reasoning (DeepSeek) | Анализ соответствия + score clamping |
| `OrchestratorService` | `services/orchestrator.py` | — | Координация pipeline |

### Адаптация и генерация

| Service | File | AI Provider | Responsibility |
|---------|------|-------------|----------------|
| `AdaptResumeService` | `services/adapt.py` | Reasoning (DeepSeek) | Адаптация резюме по checkbox_options |
| `IdealResumeService` | `services/ideal.py` | Reasoning (DeepSeek) | Генерация идеального резюме |
| `CoverLetterService` | `services/cover_letter.py` | Reasoning (DeepSeek) | Генерация сопроводительного письма |

## Детальные описания

- [ResumeService](resume_service.md)
- [VacancyService](vacancy_service.md)
- [MatchService](match_service.md)
- [OrchestratorService](orchestrator_service.md)
- [AdaptResumeService](adapt_service.md)
- [IdealResumeService](ideal_service.md)
- [CoverLetterService](cover_letter_service.md)
- [Utils](utils.md)

## Общий паттерн

Все AI-сервисы следуют одному паттерну благодаря `CachedAIService`:

```python
class SomeService(CachedAIService):
    OPERATION = "operation_name"

    def __init__(
        self,
        session: AsyncSession,
        some_repo: ISomeRepository,           # Protocol
        ai_result_repo: IAIResultRepository,  # Protocol
        ai_provider: AIProvider,              # ABC
        settings: Settings,                   # через DI
    ) -> None:
        super().__init__(session, ai_provider, settings, ai_result_repo)
        self.some_repo = some_repo

    async def process_and_cache(self, input_data: str) -> Result:
        content_hash = compute_hash(input_data)

        record = await self.some_repo.get_by_hash(content_hash)
        if record is None:
            record = await self.some_repo.create(input_data, content_hash)

        # Унифицированный кеш-through вызов:
        output_json, cache_hit = await self._call_ai_with_cache(
            content_hash, prompt
        )

        return Result(..., cache_hit=cache_hit)
```

## Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                containers.py (DI Container)                     │
│                                                                 │
│  Settings ──► AI Providers (parsing / reasoning)                │
│  Session  ──► Repositories ──► Services                         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    OrchestratorService                          │
│                                                                 │
│  run_analysis(resume_text, vacancy_text)                        │
│       │                                                         │
│       ├──► IResumeService.parse_and_cache()   ← Protocol       │
│       ├──► IVacancyService.parse_and_cache()  ← Protocol       │
│       ├──► IMatchService.analyze_and_cache()  ← Protocol       │
│       └──► IAnalysisRepository.link()         ← Protocol       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ResumeService / VacancyService / MatchService                  │
│  (наследуют CachedAIService)                                    │
│       │                                                         │
│       ├──► IResumeRepository / IVacancyRepository  ← Protocol  │
│       ├──► IAIResultRepository                     ← Protocol  │
│       └──► AIProvider                              ← ABC       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  AdaptResumeService / IdealResumeService / CoverLetterService   │
│  (наследуют CachedAIService)                                    │
│       │                                                         │
│       ├──► Multiple repos via Protocol                          │
│       ├──► Other services via Protocol                          │
│       └──► AIProvider (reasoning) ← ABC                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Кеширование

### Принцип

1. Входные данные нормализуются (`normalize_text`)
2. Вычисляется SHA256 хэш (`compute_hash`)
3. `_check_cache(hash)` → проверка `ai_result` по `(OPERATION, input_hash)`
4. Если найдено — возврат из кеша (`cache_hit=True`)
5. Если нет — `ai_provider.generate_json(prompt)` → `_save_to_cache()`

### Метод `_call_ai_with_cache()`

Полный cache-through вызов:
1. Check cache → hit? return `(output_json, True)`
2. Call AI provider
3. `_post_process_output()` hook (e.g. score clamping in MatchService)
4. Save to cache
5. Return `(output_json, False)`

### Преимущества

- **Экономия токенов** — повторные запросы бесплатны
- **Скорость** — кешированный ответ ~10мс vs ~3-5с от LLM
- **Идемпотентность** — одинаковые входы = одинаковые выходы
- **Аналитика** — все результаты сохранены в БД с provider/model

## Тестирование

Сервисы тестируются с мок-зависимостями (Protocol-based):

```python
# tests/unit/test_services.py
class TestResumeService:
    async def test_parse_returns_cached_on_hit(self):
        mock_resume_repo = AsyncMock()
        mock_ai_result_repo = AsyncMock()
        mock_ai_provider = AsyncMock()

        service = ResumeService(
            session=AsyncMock(),
            resume_repo=mock_resume_repo,
            ai_result_repo=mock_ai_result_repo,
            ai_provider=mock_ai_provider,
            settings=Settings(...),
        )

        # Assert cache_hit=True
```

**Никакого** `unittest.mock.patch` — все зависимости подменяются через конструктор.
