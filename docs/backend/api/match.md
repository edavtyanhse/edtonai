# POST /v1/match/analyze

Полный анализ соответствия резюме вакансии. Выполняет pipeline из 3 операций.

## Endpoint

```
POST /v1/match/analyze
```

## Request

### Headers

```
Content-Type: application/json
```

### Body

```json
{
  "resume_text": "string (min 10 chars)",
  "vacancy_text": "string (min 10 chars)"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume_text` | string | ✅ | Текст резюме |
| `vacancy_text` | string | ✅ | Текст вакансии |

### Example

```json
{
  "resume_text": "Иван Иванов, Python Developer. Опыт: 3 года. Навыки: Python, FastAPI, PostgreSQL, Docker, Git.",
  "vacancy_text": "Senior Python Developer. Требования: Python 5+ лет, FastAPI, PostgreSQL, Kubernetes. Желательно: микросервисы."
}
```

## Response

### Success (200)

```json
{
  "resume_id": "uuid",
  "vacancy_id": "uuid",
  "analysis_id": "uuid",
  "analysis": {
    "score": 62,
    "score_breakdown": {
      "skill_fit": {
        "value": 35,
        "comment": "Покрыты 3 из 4 обязательных навыков"
      },
      "experience_fit": {
        "value": 12,
        "comment": "3 года опыта, требуется 5+"
      },
      "ats_fit": {
        "value": 10,
        "comment": "Покрыто 5 из 7 ключевых слов"
      },
      "clarity_evidence": {
        "value": 5,
        "comment": "Навыки указаны, но без подтверждения опытом"
      }
    },
    "matched_required_skills": ["Python", "FastAPI", "PostgreSQL"],
    "missing_required_skills": ["Kubernetes"],
    "matched_preferred_skills": [],
    "missing_preferred_skills": ["микросервисы"],
    "ats": {
      "covered_keywords": ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"],
      "missing_keywords": ["Kubernetes", "микросервисы"],
      "coverage_ratio": 0.71
    },
    "gaps": [
      {
        "id": "gap_1",
        "type": "missing_skill",
        "severity": "high",
        "message": "Отсутствует Kubernetes",
        "suggestion": "Добавьте опыт работы с Kubernetes или укажите готовность изучить",
        "target_section": "skills"
      },
      {
        "id": "gap_2",
        "type": "experience_gap",
        "severity": "high",
        "message": "Требуется 5+ лет опыта, указано 3 года",
        "suggestion": "Подчеркните качество опыта и сложность проектов",
        "target_section": "experience"
      }
    ],
    "checkbox_options": [
      {
        "id": "cb_1",
        "label": "Добавить упоминание Kubernetes",
        "impact": "high",
        "action_hint": "Укажите базовое знакомство или курсы"
      },
      {
        "id": "cb_2",
        "label": "Усилить описание опыта",
        "impact": "medium",
        "action_hint": "Добавьте метрики и результаты"
      }
    ]
  },
  "cache_hit": false
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `resume_id` | UUID | ID резюме в БД |
| `vacancy_id` | UUID | ID вакансии в БД |
| `analysis_id` | UUID | ID результата анализа |
| `analysis` | object | Результат анализа от LLM |
| `cache_hit` | boolean | `true` если ВСЕ 3 операции из кеша |

### Analysis Structure

| Field | Type | Description |
|-------|------|-------------|
| `score` | int (0-100) | Общий score соответствия |
| `score_breakdown` | object | Детализация по категориям |
| `matched_required_skills` | array | Найденные обязательные навыки |
| `missing_required_skills` | array | Отсутствующие обязательные навыки |
| `matched_preferred_skills` | array | Найденные желательные навыки |
| `missing_preferred_skills` | array | Отсутствующие желательные навыки |
| `ats` | object | ATS-анализ ключевых слов |
| `gaps` | array | Список проблем/пробелов |
| `checkbox_options` | array | Опции для улучшения (Stage 2) |

### Score Breakdown (max 100)

| Category | Max Points | Description |
|----------|------------|-------------|
| `skill_fit` | 50 | Соответствие навыков |
| `experience_fit` | 25 | Соответствие опыта |
| `ats_fit` | 15 | Покрытие ATS ключевых слов |
| `clarity_evidence` | 10 | Чёткость и подтверждение |

### Gap Object

```json
{
  "id": "gap_1",
  "type": "missing_skill | experience_gap | ats_keyword | weak_evidence | weak_wording",
  "severity": "low | medium | high",
  "message": "Описание проблемы",
  "suggestion": "Рекомендация по исправлению",
  "target_section": "summary | skills | experience | education | other"
}
```

### Checkbox Option Object

```json
{
  "id": "cb_1",
  "label": "Текст для UI чекбокса",
  "impact": "low | medium | high",
  "action_hint": "Подсказка что именно изменить"
}
```

## Errors

### 422 Unprocessable Entity

Невалидные входные данные.

### 502 Bad Gateway

Ошибка AI провайдера на любом из 3 этапов.

## Flow (Pipeline)

```
┌─────────────────────────────────────────────────────────────────┐
│                    POST /v1/match/analyze                       │
│                                                                 │
│  Input: resume_text, vacancy_text                               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: ResumeService.parse_and_cache(resume_text)             │
│                                                                 │
│  • normalize(resume_text) → hash                                │
│  • ResumeRaw: get_by_hash() or create()                         │
│  • AIResult: get(parse_resume, hash) → cache hit?               │
│  • If miss: LLM(PARSE_RESUME_PROMPT) → save AIResult            │
│                                                                 │
│  Output: parsed_resume JSON                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: VacancyService.parse_and_cache(vacancy_text)           │
│                                                                 │
│  • normalize(vacancy_text) → hash                               │
│  • VacancyRaw: get_by_hash() or create()                        │
│  • AIResult: get(parse_vacancy, hash) → cache hit?              │
│  • If miss: LLM(PARSE_VACANCY_PROMPT) → save AIResult           │
│                                                                 │
│  Output: parsed_vacancy JSON                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: MatchService.analyze_and_cache(parsed_resume,          │
│                                         parsed_vacancy)         │
│                                                                 │
│  • hash = sha256(json(parsed_resume) + json(parsed_vacancy))    │
│  • AIResult: get(analyze_match, hash) → cache hit?              │
│  • If miss: LLM(ANALYZE_MATCH_PROMPT) → save AIResult           │
│                                                                 │
│  Output: analysis JSON                                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: AnalysisRepository.link(resume_id, vacancy_id,         │
│                                  analysis_result_id)            │
│                                                                 │
│  Create AnalysisLink record                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Response                                                       │
│                                                                 │
│  {                                                              │
│    resume_id, vacancy_id, analysis_id,                          │
│    analysis: {...},                                             │
│    cache_hit: (all 3 from cache?)                               │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
```

## Implementation

**File:** `backend/api/v1/match.py`

```python
@router.post("/analyze", response_model=MatchAnalyzeResponse)
async def analyze_match(
    request: MatchAnalyzeRequest,
    service: OrchestratorService = Depends(get_orchestrator_service),  # DI
) -> MatchAnalyzeResponse:
    result = await service.run_analysis(request.resume_text, request.vacancy_text)
    return MatchAnalyzeResponse(...)
```

**Dependencies:** `get_orchestrator_service` → `backend/api/dependencies.py` → DI Container

**Service:** `backend/services/orchestrator.py` → делегирует в `ResumeService`, `VacancyService`, `MatchService`
