# IdealResumeService

Сервис генерации идеального резюме-шаблона для вакансии.

## Файл

`backend/services/ideal.py`

## Класс

```python
class IdealResumeService(CachedAIService):
    OPERATION = "ideal_resume"

    def __init__(
        self,
        session: AsyncSession,
        vacancy_repo: IVacancyRepository,
        ideal_repo: IIdealResumeRepository,
        vacancy_service: IVacancyService,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        super().__init__(session, ai_provider, settings, ai_result_repo=None)
        self.vacancy_repo = vacancy_repo
        self.ideal_repo = ideal_repo
        self.vacancy_service = vacancy_service
```

## Зависимости (через DI-контейнер)

| Dependency | Interface | Provider |
|------------|-----------|----------|
| `vacancy_repo` | `IVacancyRepository` | `VacancyRepository` |
| `ideal_repo` | `IIdealResumeRepository` | `IdealResumeRepository` |
| `vacancy_service` | `IVacancyService` | `VacancyService` |
| `ai_provider` | `AIProvider` | DeepSeek (reasoning) |
| `settings` | `Settings` | Singleton |

**Примечание:** `ai_result_repo=None` — IdealResumeService использует собственный кеш через `ideal_resume` таблицу, а не общий `ai_result`.

## Основной метод

### `generate_ideal(vacancy_text=None, vacancy_id=None, options=None) -> IdealResumeResult`

## Кеширование

В отличие от других сервисов, кешируется в отдельной таблице `ideal_resume` (нужны дополнительные поля: vacancy_id, options, metadata).

## Prompt

Использует `IDEAL_RESUME_PROMPT` из `backend/integration/ai/prompts.py`.

## ⚠️ Важно

Идеальное резюме — **шаблон с выдуманным кандидатом**, используется только как референс.
