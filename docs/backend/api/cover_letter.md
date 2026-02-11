# POST /v1/cover-letter

Генерация сопроводительного письма на основе конкретной версии резюме, вакансии и результатов анализа соответствия.

## Endpoint

```
POST /v1/cover-letter
```

## Request

### Headers

```
Content-Type: application/json
Authorization: Bearer <JWT token>
```

### Body

```json
{
  "resume_version_id": "uuid",
  "options": {}
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `resume_version_id` | UUID | ✅ | ID версии резюме (из `POST /v1/versions`) |
| `options` | object | ❌ | Зарезервировано для будущих опций |

### Example

```json
{
  "resume_version_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

## Response

### Success (200)

```json
{
  "cover_letter_id": "uuid",
  "resume_version_id": "uuid",
  "vacancy_id": "uuid",
  "cover_letter_text": "Уважаемая команда...\n\nЯ пишу в ответ на вакансию Senior Python Developer...",
  "structure": {
    "opening": "Вступительный абзац с позицией и мотивацией",
    "body": "Основная аргументация: опыт, навыки, достижения",
    "closing": "Заключительный абзац с призывом к действию"
  },
  "key_points_used": [
    "3 года опыта с Python и FastAPI",
    "Опыт работы с PostgreSQL в высоконагруженных системах",
    "Лидерство команды из 4 разработчиков"
  ],
  "alignment_notes": [
    "Покрыты 3 из 4 обязательных навыков",
    "Отсутствие Kubernetes компенсировано опытом с Docker и CI/CD",
    "Недостаток лет опыта компенсирован сложностью проектов"
  ],
  "cache_hit": false
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `cover_letter_id` | UUID | ID записи в `ai_result` (для кеширования) |
| `resume_version_id` | UUID | ID использованной версии резюме |
| `vacancy_id` | UUID | ID вакансии |
| `cover_letter_text` | string | Полный текст сопроводительного письма |
| `structure` | object | Разбивка письма по структуре |
| `key_points_used` | array | Навыки и факты из резюме, использованные в письме |
| `alignment_notes` | array | Как письмо соотносится с требованиями вакансии |
| `cache_hit` | boolean | `true` если результат из кеша |

### Structure Object

| Field | Type | Description |
|-------|------|-------------|
| `opening` | string | Вступительный абзац |
| `body` | string | Основная аргументация |
| `closing` | string | Заключительный абзац |

## Errors

### 400 Bad Request

Версия резюме не найдена, вакансия не найдена, или у версии нет `analysis_id`.

```json
{
  "detail": "Resume version not found: a1b2c3d4-..."
}
```

```json
{
  "detail": "Resume version a1b2c3d4-... has no analysis_id. Cannot generate cover letter without match analysis."
}
```

### 401 Unauthorized

Отсутствует или невалидный JWT токен.

### 500 Internal Server Error

Ошибка при генерации (LLM недоступен и т.д.).

## Flow (Pipeline)

```
┌─────────────────────────────────────────────────────────────────┐
│                  POST /v1/cover-letter                           │
│                                                                  │
│  Input: resume_version_id                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: ResumeVersionRepository.get_by_id(resume_version_id)    │
│                                                                  │
│  • Получение текста адаптированного резюме                       │
│  • Получение vacancy_id и analysis_id                            │
│                                                                  │
│  Output: resume_version (text, vacancy_id, analysis_id)          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: VacancyRepository.get_by_id(vacancy_id)                 │
│                                                                  │
│  • Получение исходного текста вакансии                           │
│                                                                  │
│  Output: vacancy.source_text                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 3: AIResultRepository.get_by_id(analysis_id)               │
│                                                                  │
│  • Получение результата анализа соответствия                     │
│                                                                  │
│  Output: match_analysis JSON                                     │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 4: Compute hash & check cache                              │
│                                                                  │
│  • hash = sha256(resume_text + vacancy_text + match_analysis)    │
│  • AIResult: get("generate_cover_letter", hash) → cache hit?     │
│  • If hit → return CoverLetterResult(cache_hit=True)             │
└───────────────────────────┬─────────────────────────────────────┘
                            │ (cache miss)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 5: Build prompt & call LLM                                 │
│                                                                  │
│  • COVER_LETTER_PROMPT                                           │
│    .replace("{{RESUME_TEXT}}", resume_version.text)              │
│    .replace("{{VACANCY_TEXT}}", vacancy.source_text)             │
│    .replace("{{MATCH_ANALYSIS_JSON}}", json(match_analysis))     │
│                                                                  │
│  • ai_provider.generate_json(prompt, "generate_cover_letter")    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 6: Save to cache & return                                  │
│                                                                  │
│  • AIResultRepository.save(operation, hash, output_json, ...)    │
│  • Return CoverLetterResult(cache_hit=False)                     │
└─────────────────────────────────────────────────────────────────┘
```

## Предусловия

Для генерации сопроводительного письма необходимо:

1. **Сохранённая версия резюме** (`resume_version`) — создаётся через `POST /v1/versions` после адаптации
2. **Привязанная вакансия** — `vacancy_id` в записи версии
3. **Результат анализа** — `analysis_id` в записи версии

Типичный flow:
```
POST /v1/match/analyze → POST /v1/resumes/adapt → POST /v1/versions → POST /v1/cover-letter
```

## Кеширование

Хэш вычисляется по тройке `(resume_version_text, vacancy_text, match_analysis)`.
Одинаковые входные данные → одинаковое письмо из кеша.

## Implementation

**API:** `backend/api/v1/cover_letter.py`

**Service:** `backend/services/cover_letter.py` → `CoverLetterService.generate_cover_letter()`

**Prompt:** `backend/prompts.py` → `COVER_LETTER_PROMPT`
