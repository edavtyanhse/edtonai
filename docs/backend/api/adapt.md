# POST /v1/resumes/adapt

Адаптация резюме под вакансию по выбранным улучшениям (checkbox_options из analyze_match).

## Endpoint

```
POST /v1/resumes/adapt
```

## Request

### Headers

```
Content-Type: application/json
```

### Body

```json
{
  "resume_id": "uuid (или resume_text)",
  "vacancy_id": "uuid (или vacancy_text)",
  "selected_improvements": [
    {
      "checkbox_id": "cb_1",
      "user_input": "Optional text",
      "ai_generate": false
    }
  ],
  "selected_checkbox_ids": ["cb_1", "cb_2"],
  "base_version_id": "uuid (опционально)",
  "options": {
    "language": "ru | en | auto",
    "template": "default | harvard"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume_id` | UUID | ✅* | ID резюме из БД |
| `resume_text` | string | ✅* | Текст резюме (альтернатива resume_id) |
| `vacancy_id` | UUID | ✅* | ID вакансии из БД |
| `vacancy_text` | string | ✅* | Текст вакансии (альтернатива vacancy_id) |
| `selected_improvements` | list[object] | ✅** | Список улучшений с опциональным user_input |
| `selected_checkbox_ids` | list[str] | ✅** | DEPRECATED: IDs улучшений (для обратной совместимости) |
| `base_version_id` | UUID | ❌ | ID родительской версии (для цепочки) |
| `options` | object | ❌ | Настройки адаптации |

*Требуется либо `*_id`, либо `*_text` для резюме и вакансии.
**Требуется либо `selected_improvements`, либо `selected_checkbox_ids` (deprecated).

> **Примечание:** `selected_checkbox_ids` поддерживается для обратной совместимости, но рекомендуется использовать `selected_improvements` для более гибкого управления улучшениями (с user_input и ai_generate флагами).

### Пример минимального запроса (новый формат)

```json
{
  "resume_id": "94367c01-d06c-46ea-99f8-293070552b69",
  "vacancy_id": "b86a0150-35c8-40a5-a651-c9fdd720310f",
  "selected_improvements": [
    {
      "checkbox_id": "detail_tech_exp",
      "user_input": null,
      "ai_generate": false
    },
    {
      "checkbox_id": "add_ceremonies",
      "user_input": "Участвовал в daily standup, sprint planning",
      "ai_generate": false
    }
  ]
}
```

### Пример запроса (legacy формат)

```json
{
  "resume_id": "94367c01-d06c-46ea-99f8-293070552b69",
  "vacancy_id": "b86a0150-35c8-40a5-a651-c9fdd720310f",
  "selected_checkbox_ids": ["detail_tech_exp", "add_ceremonies"]
}
```

## Response

### Success (200)

```json
{
  "version_id": "d97cdd84-505e-47ec-bf0e-2d2a607040aa",
  "parent_version_id": null,
  "resume_id": "94367c01-d06c-46ea-99f8-293070552b69",
  "vacancy_id": "b86a0150-35c8-40a5-a651-c9fdd720310f",
  "updated_resume_text": "Полный текст адаптированного резюме...",
  "change_log": [
    {
      "checkbox_id": "detail_tech_exp",
      "what_changed": "Добавлено упоминание Agile-церемоний",
      "where": "experience",
      "before_excerpt": "Работал в команде",
      "after_excerpt": "Работал в кросс-функциональной команде, участвовал в daily standup, sprint planning, retrospective"
    }
  ],
  "applied_checkbox_ids": ["detail_tech_exp", "add_ceremonies"],
  "cache_hit": false
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `version_id` | UUID | ID созданной версии резюме |
| `parent_version_id` | UUID? | ID родительской версии (null если первая адаптация) |
| `resume_id` | UUID | ID базового резюме |
| `vacancy_id` | UUID | ID целевой вакансии |
| `updated_resume_text` | string | Полный текст адаптированного резюме |
| `change_log` | list | Список изменений с деталями |
| `applied_checkbox_ids` | list[str] | IDs успешно применённых улучшений |
| `cache_hit` | bool | True если результат из кеша |

### ChangeLogEntry Structure

| Field | Type | Description |
|-------|------|-------------|
| `checkbox_id` | string | ID улучшения |
| `what_changed` | string | Описание изменения |
| `where` | string | Секция: summary, skills, experience, education, other |
| `before_excerpt` | string? | Фрагмент до изменения |
| `after_excerpt` | string? | Фрагмент после изменения |

## Pipeline

```
adapt_resume(resume_id, vacancy_id, selected_checkbox_ids)
│
├── 1. Get resume from DB (or parse if text provided)
├── 2. Get vacancy from DB (or parse if text provided)
├── 3. Validate base_version_id (if provided, must exist)
├── 4. Get parsed_resume from cache
├── 5. Get parsed_vacancy from cache
├── 6. Get match_analysis from cache
├── 7. Compute input_hash
├── 8. Check adapt_resume cache
│     │
│     ├── Cache hit → create ResumeVersion → return
│     │
│     └── Cache miss ↓
│
├── 9. Build prompt with:
│     - Original resume text
│     - Parsed resume JSON
│     - Parsed vacancy JSON
│     - Analysis with gaps
│     - Selected checkbox IDs
│
├── 10. Call LLM (DeepSeek) with GENERATE_UPDATED_RESUME_PROMPT
│
├── 11. Save to ai_result cache
│
├── 12. Create ResumeVersion record
│
└── 13. Return result
```

## Caching

Кеш вычисляется по хэшу:
- Оригинальный текст резюме
- Parsed resume JSON
- Parsed vacancy JSON
- Analysis JSON
- Sorted selected_checkbox_ids
- Options (language, template)

Повторный запрос с теми же параметрами вернёт `cache_hit: true`.

## Version History

Каждый вызов создаёт запись в `resume_version`:
- `parent_version_id` позволяет построить цепочку версий
- Можно откатиться к предыдущей версии по ID
- История сохраняется для каждой пары resume + vacancy

## Error Responses

### 422 - Validation Error

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body", "selected_checkbox_ids"],
      "msg": "Field required"
    }
  ]
}
```

### 500 - Internal Error

```json
{
  "detail": "Resume not found: 94367c01-d06c-46ea-99f8-293070552b69"
}
```

## Implementation

**File:** `backend/api/v1/adapt.py`

```python
@router.post("/adapt", response_model=AdaptResumeResponse)
async def adapt_resume(
    request: AdaptResumeRequest,
    service: AdaptResumeService = Depends(get_adapt_resume_service),  # DI
) -> AdaptResumeResponse:
    result = await service.adapt_and_version(...)
    return AdaptResumeResponse(...)
```

**Dependencies:** `get_adapt_resume_service` → `backend/api/dependencies.py` → DI Container

**Service:** `backend/services/adapt.py` → `CachedAIService`
