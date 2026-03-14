# POST /v1/resumes/parse

Парсинг текста резюме в структурированный JSON.

## Endpoint

```
POST /v1/resumes/parse
```

## Request

### Headers

```
Content-Type: application/json
```

### Body

```json
{
  "resume_text": "string (min 10 chars)"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume_text` | string | ✅ | Текст резюме (минимум 10 символов) |

### Example

```json
{
  "resume_text": "Иван Иванов\nPython Developer\n\nОпыт работы:\n- ООО Рога и Копыта (2020-2024): Backend разработчик\n  Python, FastAPI, PostgreSQL\n\nНавыки: Python, FastAPI, Django, PostgreSQL, Docker, Git"
}
```

## Response

### Success (200)

```json
{
  "resume_id": "uuid",
  "resume_hash": "string (sha256)",
  "parsed_resume": {
    "personal_info": {
      "name": "Иван Иванов",
      "title": "Python Developer",
      "location": null,
      "contacts": {
        "email": null,
        "phone": null,
        "links": []
      }
    },
    "summary": null,
    "skills": [
      {
        "name": "Python",
        "category": "language",
        "level": "unknown"
      },
      {
        "name": "FastAPI",
        "category": "framework",
        "level": "unknown"
      }
    ],
    "work_experience": [
      {
        "company": "ООО Рога и Копыта",
        "position": "Backend разработчик",
        "start_date": "2020",
        "end_date": "2024",
        "responsibilities": [],
        "achievements": [],
        "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
      }
    ],
    "education": [],
    "certifications": [],
    "languages": [],
    "raw_sections": {}
  },
  "cache_hit": false
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `resume_id` | UUID | ID записи в БД |
| `resume_hash` | string | SHA256 хэш нормализованного текста |
| `parsed_resume` | object | Структурированное резюме от LLM |
| `cache_hit` | boolean | `true` если из кеша |

### Parsed Resume Structure

См. [Resume Schema](../schemas/parsed_resume.md)

## Errors

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "resume_text"],
      "msg": "String should have at least 10 characters",
      "input": "short"
    }
  ]
}
```

### 502 Bad Gateway

```json
{
  "detail": "AI provider error: DeepSeek request failed after retries: ..."
}
```

## Flow

```
1. Нормализация текста (trim, collapse spaces)
2. Вычисление SHA256 хэша
3. Поиск ResumeRaw по хэшу → создание если нет
4. Поиск AIResult(operation=parse_resume, input_hash) → cache hit?
5. Если нет → вызов LLM с PARSE_RESUME_PROMPT
6. Сохранение AIResult
7. Возврат результата
```

## Implementation

**File:** `backend/api/v1/resumes.py`

```python
@router.post("/parse", response_model=ResumeParseResponse)
async def parse_resume(
    request: ResumeParseRequest,
    service: ResumeService = Depends(get_resume_service),  # DI
) -> ResumeParseResponse:
    result = await service.parse_and_cache(request.resume_text)
    return ResumeParseResponse(...)
```

**Dependencies:** `get_resume_service` → `backend/api/dependencies.py` → DI Container

**Service:** `backend/services/resume.py` → `CachedAIService`
