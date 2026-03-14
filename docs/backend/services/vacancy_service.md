# VacancyService

Сервис парсинга и кеширования вакансий.

## Файл

`backend/services/vacancy.py`

## Класс

```python
class VacancyService(CachedAIService):
    OPERATION = "parse_vacancy"

    def __init__(
        self,
        session: AsyncSession,
        vacancy_repo: IVacancyRepository,
        ai_result_repo: IAIResultRepository,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        super().__init__(session, ai_provider, settings, ai_result_repo)
        self.vacancy_repo = vacancy_repo
```

## Зависимости (через DI-контейнер)

| Dependency | Interface | Provider |
|------------|-----------|----------|
| `vacancy_repo` | `IVacancyRepository` | `VacancyRepository` |
| `ai_result_repo` | `IAIResultRepository` | `AIResultRepository` |
| `ai_provider` | `AIProvider` | Groq (parsing) |
| `settings` | `Settings` | Singleton |

## Методы

### `parse_and_cache(vacancy_text: str, source_url: str = None) -> VacancyParseResult`

Парсит текст вакансии и возвращает структурированный JSON.

#### Возвращает

```python
@dataclass
class VacancyParseResult:
    vacancy_id: UUID
    vacancy_hash: str
    parsed_vacancy: dict
    cache_hit: bool
```

#### Алгоритм

Аналогичен `ResumeService.parse_and_cache()`:

1. Нормализация и хэширование текста
2. Get or create `VacancyRaw`
3. `_check_cache(hash)` → from CachedAIService
4. Если miss — вызов LLM с `PARSE_VACANCY_PROMPT` через Groq
5. `_save_to_cache()` → сохранение в `ai_result`
6. Update vacancy parsed fields via `domain/mappers.py`
7. Возврат `VacancyParseResult`

## Prompt

Использует `PARSE_VACANCY_PROMPT` из `backend/integration/ai/prompts.py`.

## Скрапинг URL

Если вместо текста передан URL, `api/v1/vacancies.py` вызывает `WebScraper.fetch_text(url)` перед сервисом. При ошибке URL бросается `ScraperError` (обрабатывается глобально).
