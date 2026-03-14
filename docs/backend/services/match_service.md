# MatchService

Сервис анализа соответствия резюме вакансии.

## Файл

`backend/services/match.py`

## Класс

```python
class MatchService(CachedAIService):
    OPERATION = "analyze_match"

    _SCORE_LIMITS: ClassVar[dict] = {
        "skill_fit": 50, "experience_fit": 25,
        "ats_fit": 15, "clarity_evidence": 10,
    }

    def __init__(
        self,
        session: AsyncSession,
        ai_result_repo: IAIResultRepository,
        ai_provider: AIProvider,
        settings: Settings,
    ) -> None:
        super().__init__(session, ai_provider, settings, ai_result_repo)
```

## Зависимости (через DI-контейнер)

| Dependency | Interface | Provider |
|------------|-----------|----------|
| `ai_result_repo` | `IAIResultRepository` | `AIResultRepository` |
| `ai_provider` | `AIProvider` | DeepSeek (reasoning) |
| `settings` | `Settings` | Singleton |

**Примечание:** MatchService не работает с `ResumeRaw` или `VacancyRaw` напрямую — принимает уже распарсенные JSON.

## Методы

### `analyze_and_cache(parsed_resume, parsed_vacancy) -> MatchAnalysisResult`

#### Возвращает

```python
@dataclass
class MatchAnalysisResult:
    analysis_id: UUID
    analysis: dict
    cache_hit: bool
```

#### Алгоритм

```
analyze_and_cache(parsed_resume, parsed_vacancy)
│
├── 1. _compute_match_hash(parsed_resume, parsed_vacancy)
├── 2. _call_ai_with_cache(hash, prompt) → from CachedAIService
│     ├── _check_cache → hit? return (output_json, True)
│     ├── ai_provider.generate_json → DeepSeek
│     ├── _post_process_output → score clamping!
│     └── _save_to_cache → return (output_json, False)
└── 3. return MatchAnalysisResult
```

## Score Clamping

`MatchService` переопределяет hook `_post_process_output()` для валидации scores:

```python
def _post_process_output(self, output_json: dict) -> dict:
    return self._clamp_scores(output_json)

@staticmethod
def _clamp_scores(analysis: dict) -> dict:
    """Clamp score_breakdown values to their defined maximums."""
    # skill_fit: max 50, experience_fit: max 25, ats_fit: max 15, clarity_evidence: max 10
    # total score: max 100
```

Это гарантирует, что LLM не вернёт scores выше допустимых пределов.

## Scoring Formula

| Category | Max Points | Description |
|----------|------------|-------------|
| `skill_fit` | 50 | Соответствие навыков |
| `experience_fit` | 25 | Соответствие опыта |
| `ats_fit` | 15 | Покрытие ATS ключевых слов |
| `clarity_evidence` | 10 | Чёткость и подтверждение |

## Prompt

Использует `ANALYZE_MATCH_PROMPT` из `backend/integration/ai/prompts.py`.
