# AdaptResumeService

Сервис адаптации резюме под вакансию по выбранным улучшениям.

## Файл

`backend/services/adapt.py`

## Класс

```python
class AdaptResumeService(CachedAIService):
    OPERATION = "adapt_resume"

    def __init__(
        self,
        session: AsyncSession,
        resume_repo: IResumeRepository,
        vacancy_repo: IVacancyRepository,
        ai_result_repo: IAIResultRepository,
        version_repo: IResumeVersionRepository,
        resume_service: IResumeService,
        vacancy_service: IVacancyService,
        match_service: IMatchService,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        super().__init__(session, ai_provider, settings, ai_result_repo)
        self.resume_repo = resume_repo
        self.vacancy_repo = vacancy_repo
        self.version_repo = version_repo
        self.resume_service = resume_service
        self.vacancy_service = vacancy_service
        self.match_service = match_service
```

## Зависимости (через DI-контейнер)

| Dependency | Interface | Provider |
|------------|-----------|----------|
| `resume_repo` | `IResumeRepository` | `ResumeRepository` |
| `vacancy_repo` | `IVacancyRepository` | `VacancyRepository` |
| `ai_result_repo` | `IAIResultRepository` | `AIResultRepository` |
| `version_repo` | `IResumeVersionRepository` | `ResumeVersionRepository` |
| `resume_service` | `IResumeService` | `ResumeService` |
| `vacancy_service` | `IVacancyService` | `VacancyService` |
| `match_service` | `IMatchService` | `MatchService` |
| `ai_provider` | `AIProvider` | DeepSeek (reasoning) |
| `settings` | `Settings` | Singleton |

## Основной метод

### `adapt_and_version()`

```python
async def adapt_and_version(
    self,
    resume_text=None, resume_id=None,
    vacancy_text=None, vacancy_id=None,
    selected_checkbox_ids=None,
    base_version_id=None,
    options=None,
) -> AdaptResumeResult
```

## Pipeline

```
adapt_and_version()
│
├── 1. Получить резюме (resume_id или parse текст)
├── 2. Получить вакансию (vacancy_id или parse текст)
├── 3. Получить parsed_resume, parsed_vacancy, match_analysis
├── 4. Вычислить input_hash
├── 5. _check_cache(hash) → from CachedAIService
│     ├── Hit → создать ResumeVersion → return
│     └── Miss ↓
├── 6. Build prompt (GENERATE_UPDATED_RESUME_PROMPT)
├── 7. ai_provider.generate_json → DeepSeek
├── 8. _save_to_cache(hash, output_json)
├── 9. Создать ResumeVersion record
└── 10. Return AdaptResumeResult
```

## Prompt

Использует `GENERATE_UPDATED_RESUME_PROMPT` из `backend/integration/ai/prompts.py`.

## Version History

Каждый вызов создаёт запись в `resume_version` с `parent_version_id` для цепочки версий.
