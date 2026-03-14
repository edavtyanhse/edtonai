# POST /v1/vacancies/parse

Парсинг текста вакансии в структурированный JSON.

## Endpoint

```
POST /v1/vacancies/parse
```

## Request

### Headers

```
Content-Type: application/json
```

### Body

```json
{
  "vacancy_text": "string (min 10 chars)"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `vacancy_text` | string | ✅ | Текст вакансии (минимум 10 символов) |

### Example

```json
{
  "vacancy_text": "Senior Python Developer\n\nКомпания: TechCorp\n\nТребования:\n- Python 5+ лет\n- FastAPI или Django\n- PostgreSQL\n- Docker, Kubernetes\n- Английский B2+\n\nЖелательно:\n- Опыт с микросервисами\n- CI/CD\n\nОбязанности:\n- Разработка backend API\n- Code review\n- Менторинг джунов"
}
```

## Response

### Success (200)

```json
{
  "vacancy_id": "uuid",
  "vacancy_hash": "string (sha256)",
  "parsed_vacancy": {
    "job_title": "Senior Python Developer",
    "company": "TechCorp",
    "employment_type": null,
    "location": null,
    "required_skills": [
      {
        "name": "Python",
        "type": "hard",
        "evidence": "Python 5+ лет"
      },
      {
        "name": "FastAPI",
        "type": "hard",
        "evidence": "FastAPI или Django"
      },
      {
        "name": "PostgreSQL",
        "type": "hard",
        "evidence": "PostgreSQL"
      }
    ],
    "preferred_skills": [
      {
        "name": "Microservices",
        "type": "hard",
        "evidence": "Опыт с микросервисами"
      }
    ],
    "experience_requirements": {
      "min_years": 5,
      "details": "Python 5+ лет"
    },
    "responsibilities": [
      "Разработка backend API",
      "Code review",
      "Менторинг джунов"
    ],
    "ats_keywords": [
      "Python", "FastAPI", "Django", "PostgreSQL",
      "Docker", "Kubernetes", "CI/CD", "микросервисы"
    ]
  },
  "cache_hit": false
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `vacancy_id` | UUID | ID записи в БД |
| `vacancy_hash` | string | SHA256 хэш нормализованного текста |
| `parsed_vacancy` | object | Структурированная вакансия от LLM |
| `cache_hit` | boolean | `true` если из кеша |

### Parsed Vacancy Structure

| Field | Type | Description |
|-------|------|-------------|
| `job_title` | string\|null | Название должности |
| `company` | string\|null | Компания |
| `employment_type` | string\|null | Тип занятости |
| `location` | string\|null | Локация/удалёнка |
| `required_skills` | array | Обязательные навыки |
| `preferred_skills` | array | Желательные навыки |
| `experience_requirements` | object | Требования к опыту |
| `responsibilities` | array | Обязанности |
| `ats_keywords` | array | Ключевые слова для ATS |

### Skill Object

```json
{
  "name": "Python",
  "type": "hard | soft | domain | tool",
  "evidence": "фрагмент из вакансии"
}
```

## Errors

### 422 Unprocessable Entity

```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "vacancy_text"],
      "msg": "String should have at least 10 characters"
    }
  ]
}
```

### 502 Bad Gateway

```json
{
  "detail": "AI provider error: ..."
}
```

## Flow

```
1. Нормализация текста
2. Вычисление SHA256 хэша
3. Поиск VacancyRaw по хэшу → создание если нет
4. Поиск AIResult(operation=parse_vacancy, input_hash)
5. Если нет → вызов LLM с PARSE_VACANCY_PROMPT
6. Сохранение AIResult
7. Возврат результата
```

## Implementation

**File:** `backend/api/v1/vacancies.py`

```python
@router.post("/parse", response_model=VacancyParseResponse)
async def parse_vacancy(
    request: VacancyParseRequest,
    service: VacancyService = Depends(get_vacancy_service),  # DI
) -> VacancyParseResponse:
    # supports URL scraping: if no text but url provided, scrapes it
    result = await service.parse_and_cache(text, source_url=source_url)
    return VacancyParseResponse(...)
```

**Dependencies:** `get_vacancy_service` → `backend/api/dependencies.py` → DI Container

**Service:** `backend/services/vacancy.py` → `CachedAIService`
