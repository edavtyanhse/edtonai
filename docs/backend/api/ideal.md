# POST /v1/resumes/ideal

Генерация идеального резюме-шаблона для вакансии. Показывает, как должно выглядеть идеальное резюме кандидата.

## Endpoint

```
POST /v1/resumes/ideal
```

## Request

### Headers

```
Content-Type: application/json
```

### Body

```json
{
  "vacancy_id": "uuid (или vacancy_text)",
  "options": {
    "language": "ru | en | auto",
    "template": "default | harvard",
    "seniority": "junior | middle | senior | any"
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vacancy_id` | UUID | ✅* | ID вакансии из БД |
| `vacancy_text` | string | ✅* | Текст вакансии (альтернатива vacancy_id) |
| `options` | object | ❌ | Настройки генерации |

*Требуется либо `vacancy_id`, либо `vacancy_text`.

### Options

| Option | Values | Default | Description |
|--------|--------|---------|-------------|
| `language` | ru, en, auto | auto | Язык резюме |
| `template` | default, harvard | default | Стиль шаблона |
| `seniority` | junior, middle, senior, any | any | Уровень кандидата |

### Пример минимального запроса

```json
{
  "vacancy_id": "b86a0150-35c8-40a5-a651-c9fdd720310f"
}
```

## Response

### Success (200)

```json
{
  "ideal_id": "a1b2c3d4-5678-90ab-cdef-1234567890ab",
  "vacancy_id": "b86a0150-35c8-40a5-a651-c9fdd720310f",
  "ideal_resume_text": "Иван Иванов\nSenior Python Developer\n\nО себе:\n...",
  "metadata": {
    "keywords_used": ["Python", "FastAPI", "PostgreSQL", "Docker", "Kubernetes"],
    "structure": ["summary", "skills", "experience", "education", "certifications"],
    "assumptions": [
      "Кандидат имеет 5+ лет опыта Python",
      "Опыт работы с микросервисной архитектурой"
    ],
    "language": "ru",
    "template": "default"
  },
  "cache_hit": false
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `ideal_id` | UUID | ID записи идеального резюме |
| `vacancy_id` | UUID | ID вакансии |
| `ideal_resume_text` | string | Полный текст идеального резюме |
| `metadata` | object | Метаданные генерации |
| `cache_hit` | bool | True если результат из кеша |

### Metadata Structure

| Field | Type | Description |
|-------|------|-------------|
| `keywords_used` | list[str] | ATS-ключевые слова, включённые в резюме |
| `structure` | list[str] | Секции, использованные в резюме |
| `assumptions` | list[str] | Допущения при генерации |
| `language` | string | Язык сгенерированного резюме |
| `template` | string | Использованный шаблон |

## Pipeline

```
ideal_resume(vacancy_id, options)
│
├── 1. Get vacancy from DB (or parse if text provided)
│
├── 2. Get parsed_vacancy from cache
│
├── 3. Compute input_hash (vacancy_hash + options)
│
├── 4. Check ideal_resume table by input_hash
│     │
│     ├── Cache hit → return existing record
│     │
│     └── Cache miss ↓
│
├── 5. Build prompt with:
│     - Parsed vacancy JSON
│     - Options (language, template, seniority)
│
├── 6. Call LLM (DeepSeek) with IDEAL_RESUME_PROMPT
│
├── 7. Create IdealResume record
│
└── 8. Return result
```

## Caching

Кеш по `input_hash`:
- vacancy_hash (SHA256 текста вакансии)
- options (language, template, seniority)

Повторный запрос с теми же параметрами вернёт `cache_hit: true`.

## Use Cases

### 1. Эталон для сравнения

Показать кандидату "идеальное резюме" для понимания, чего не хватает.

### 2. Вдохновение для формулировок

Кандидат может заимствовать фразы и структуру.

### 3. Обучение HR/Recruiter

Понимание, какие навыки и опыт искать.

## Important Notes

⚠️ **Идеальное резюме — это шаблон, а не реальный человек!**

- Генерируется на основе требований вакансии
- Содержит "идеального" кандидата с выдуманным опытом
- Используется только как референс

## Error Responses

### 422 - Validation Error

```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["body"],
      "msg": "Either vacancy_text or vacancy_id must be provided"
    }
  ]
}
```

### 500 - Internal Error

```json
{
  "detail": "Vacancy not found: b86a0150-35c8-40a5-a651-c9fdd720310f"
}
```

## Implementation

**File:** `backend/api/v1/ideal.py`

```python
@router.post("/ideal", response_model=IdealResumeResponse)
async def generate_ideal_resume(
    request: IdealResumeRequest,
    service: IdealResumeService = Depends(get_ideal_resume_service),  # DI
) -> IdealResumeResponse:
    result = await service.generate_ideal(...)
    return IdealResumeResponse(...)
```

**Dependencies:** `get_ideal_resume_service` → `backend/api/dependencies.py` → DI Container

**Service:** `backend/services/ideal.py` → `CachedAIService`
