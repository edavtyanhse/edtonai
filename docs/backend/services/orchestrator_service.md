# OrchestratorService

Сервис-координатор полного пайплайна анализа «резюме ↔ вакансия».

## Файл

`backend/services/orchestrator.py`

## Класс

```python
class OrchestratorService:
    """Orchestrates the full resume-vacancy analysis pipeline."""

    def __init__(
        self,
        session: AsyncSession,
        resume_service: IResumeService,
        vacancy_service: IVacancyService,
        match_service: IMatchService,
        analysis_repo: IAnalysisRepository,
    ) -> None:
```

> **Не наследуется от `CachedAIService`** — Orchestrator не вызывает AI напрямую, а делегирует вложенным сервисам.

## Зависимости (через DI-контейнер)

| Dependency | Interface | Provider |
|------------|-----------|----------|
| `resume_service` | `IResumeService` | `ResumeService` |
| `vacancy_service` | `IVacancyService` | `VacancyService` |
| `match_service` | `IMatchService` | `MatchService` |
| `analysis_repo` | `IAnalysisRepository` | `AnalysisRepository` |

## Основной метод

### `run_analysis(resume_text, vacancy_text) -> FullAnalysisResult`

Полный пайплайн из 4 шагов:

1. **Parse resume** → `resume_service.parse_and_cache(resume_text)` → `ResumeResult`
2. **Parse vacancy** → `vacancy_service.parse_and_cache(vacancy_text)` → `VacancyResult`
3. **Analyze match** → `match_service.analyze_and_cache(parsed_resume, parsed_vacancy)` → `MatchResult`
4. **Create link** → `analysis_repo.link(resume_id, vacancy_id, analysis_result_id)`

Возвращает `FullAnalysisResult` с флагом `cache_hit` (true только если все 3 подзапроса были cache hit).

## Диаграмма

```
Orchestrator
  ├── ResumeService.parse_and_cache()    [Groq - parsing]
  ├── VacancyService.parse_and_cache()   [Groq - parsing]
  ├── MatchService.analyze_and_cache()   [DeepSeek - reasoning]
  └── AnalysisRepository.link()          [DB only]
```

## Логирование

Каждый шаг логируется через `self.logger` с id результата и cache_hit статусом.
