# API Specification

REST API для сервиса адаптации резюме под вакансию.

## Base URL

```
http://localhost:8000
```

## Endpoints Overview

### Stage 1: Парсинг и анализ

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/v1/resumes/parse` | Парсинг резюме |
| POST | `/v1/vacancies/parse` | Парсинг вакансии |
| POST | `/v1/match/analyze` | Полный анализ соответствия |

### Stage 2: Адаптация и генерация

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/v1/resumes/adapt` | Адаптация резюме по выбранным улучшениям |
| POST | `/v1/resumes/ideal` | Генерация идеального резюме для вакансии |
| POST | `/v1/cover-letter` | Генерация сопроводительного письма |

## Детальные спецификации

- [Resumes API](resumes.md) — парсинг резюме
- [Vacancies API](vacancies.md) — парсинг вакансий
- [Match API](match.md) — анализ соответствия
- [Adapt API](adapt.md) — адаптация резюме (Stage 2)
- [Ideal API](ideal.md) — идеальное резюме (Stage 2)
- [Cover Letter API](cover_letter.md) — сопроводительное письмо (Stage 2)

## Общие принципы

### Content-Type

Все запросы и ответы используют `application/json`.

### Коды ответов

| Code | Description | Handler |
|------|-------------|--------|
| 200 | Успешный запрос | — |
| 400 | Business error (`AppError`) или `ValueError` | `app_error_handler` / `value_error_handler` |
| 404 | Not found (`AppError` с status 404) | `app_error_handler` |
| 422 | Validation error (невалидный JSON / Pydantic) | FastAPI built-in |
| 500 | Internal server error | — |
| 502 | AI provider error (`AIError`) | `ai_error_handler` |

Обработчики ошибок зарегистрированы в `backend/errors/handlers.py` → `register_exception_handlers(app)`.

### Заголовки

**Request:**
```
Content-Type: application/json
X-Request-ID: <optional, для трейсинга>
```

**Response:**
```
Content-Type: application/json
X-Request-ID: <echo или generated>
```

### Dependency Injection

Все эндпоинты получают сервисы через DI-контейнер:

```python
@router.post("/parse")
async def parse_resume(
    request: ResumeParseRequest,
    service: ResumeService = Depends(get_resume_service),  # ← из DI
) -> ResumeParseResponse:
```

Dependency-функции определены в `backend/api/dependencies.py` и используют `@inject` + `Provide[Container.xxx_service]`.

### Кеширование

Все LLM-операции кешируются по SHA256 хэшу входных данных (через `CachedAIService`).

Ответ содержит поле `cache_hit`:
- `true` — результат из кеша, LLM не вызывался
- `false` — свежий результат от LLM

### Примеры ошибок

**AppError (400/404):**
```json
{
  "detail": "Resume not found: 94367c01-..."
}
```

**AIError (502):**
```json
{
  "detail": "AI provider error: DeepSeek request failed after retries: ..."
}
```

или для validation errors:

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "resume_text"],
      "msg": "String should have at least 10 characters",
      "input": "short",
      "ctx": {"min_length": 10}
    }
  ]
}
```
