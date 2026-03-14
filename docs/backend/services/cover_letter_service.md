# CoverLetterService

Сервис генерации сопроводительного письма на основе адаптированной версии резюме.

## Файл

`backend/services/cover_letter.py`

## Класс

```python
class CoverLetterService(CachedAIService):
    OPERATION = "generate_cover_letter"

    def __init__(
        self,
        session: AsyncSession,
        ai_result_repo: IAIResultRepository,
        version_repo: IResumeVersionRepository,
        user_version_repo: IUserVersionRepository,
        vacancy_repo: IVacancyRepository,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        super().__init__(
            session=session,
            ai_provider=ai_provider,
            settings=settings,
            ai_result_repo=ai_result_repo,
        )
        self.version_repo = version_repo
        self.user_version_repo = user_version_repo
        self.vacancy_repo = vacancy_repo
```

## Зависимости (через DI-контейнер)

| Dependency | Interface | Provider |
|------------|-----------|----------|
| `ai_result_repo` | `IAIResultRepository` | `AIResultRepository` |
| `version_repo` | `IResumeVersionRepository` | `ResumeVersionRepository` |
| `user_version_repo` | `IUserVersionRepository` | `UserVersionRepository` |
| `vacancy_repo` | `IVacancyRepository` | `VacancyRepository` |
| `ai_provider` | `AIProvider` | DeepSeek (reasoning) |
| `settings` | `Settings` | Singleton |

## Основной метод

### `generate(resume_version_id, vacancy_id, match_analysis, user_id) -> CoverLetterResult`

1. Загружает данные `resume_version`, `user_version`, `vacancy` через Protocol-typed репозитории
2. Вычисляет хеш: `_compute_cover_letter_hash(resume_text, vacancy_text, match_analysis, provider, model, prompt_template)`
3. Проверяет кеш через `_check_cache(hash)`
4. Если кеша нет — формирует prompt из `COVER_LETTER_PROMPT`, вызывает AI
5. Сохраняет результат через `_save_to_cache(hash, result)`
6. Возвращает `CoverLetterResult`

## Кеширование

Использует стандартный `ai_result` кеш (через `IAIResultRepository`).

Хеш включает:
- Текст версии резюме
- Текст вакансии
- Match analysis (JSON, sorted)
- Provider / model
- SHA256 prompt-шаблона

## Prompt

`COVER_LETTER_PROMPT` из `backend/integration/ai/prompts.py`.
