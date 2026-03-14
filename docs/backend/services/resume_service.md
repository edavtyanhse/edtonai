# ResumeService

Сервис парсинга и кеширования резюме.

## Файл

`backend/services/resume.py`

## Класс

```python
class ResumeService(CachedAIService):
    OPERATION = "parse_resume"

    def __init__(
        self,
        session: AsyncSession,
        resume_repo: IResumeRepository,
        ai_result_repo: IAIResultRepository,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        super().__init__(session, ai_provider, settings, ai_result_repo)
        self.resume_repo = resume_repo
```

## Зависимости (через DI-контейнер)

| Dependency | Interface | Provider |
|------------|-----------|----------|
| `resume_repo` | `IResumeRepository` | `ResumeRepository` |
| `ai_result_repo` | `IAIResultRepository` | `AIResultRepository` |
| `ai_provider` | `AIProvider` | Groq (parsing) |
| `settings` | `Settings` | Singleton |

## Методы

### `parse_and_cache(resume_text: str) -> ResumeParseResult`

Парсит текст резюме и возвращает структурированный JSON.

#### Возвращает

```python
@dataclass
class ResumeParseResult:
    resume_id: UUID
    resume_hash: str
    parsed_resume: dict
    cache_hit: bool
```

#### Алгоритм

```
parse_and_cache(resume_text)
│
├── 1. compute_hash(resume_text)
├── 2. resume_repo.get_by_hash(hash) → get or create
├── 3. _check_cache(hash) → from CachedAIService
│     ├── Hit → return ResumeParseResult(cache_hit=True)
│     └── Miss ↓
├── 4. Build prompt (PARSE_RESUME_PROMPT)
├── 5. ai_provider.generate_json(prompt) → Groq
├── 6. _save_to_cache(hash, output_json)
├── 7. Update resume.parsed_at + parsed fields via domain/mappers.py
└── 8. return ResumeParseResult(cache_hit=False)
```

## Prompt

Использует `PARSE_RESUME_PROMPT` из `backend/integration/ai/prompts.py`.

## Ошибки

| Exception | Cause | HTTP Code |
|-----------|-------|-----------|
| `AIRequestError` | Провайдер недоступен | 502 |
| `AIResponseFormatError` | Невалидный JSON от LLM | 502 |

Все обрабатываются глобально в `errors/handlers.py`.
