# Database Documentation

PostgreSQL схема данных.

## Содержание

- [ERD Diagram](erd.puml) — PlantUML диаграмма
- [Tables](#tables) — описание таблиц
- [Indexes](#indexes) — индексы
- [Relationships](#relationships) — связи

## ERD

![ERD](erd.puml)

Для просмотра: установите PlantUML extension в VS Code или используйте [PlantUML Online](https://www.plantuml.com/plantuml/uml/).

## Tables

### Stage 1: Core Tables

#### resume_raw

Хранит исходные тексты резюме.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK, DEFAULT uuid_generate_v4() | Уникальный ID |
| `source_text` | TEXT | NOT NULL | Исходный текст резюме |
| `content_hash` | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | SHA256 нормализованного текста |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Время создания |

#### vacancy_raw

Хранит исходные тексты вакансий.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Уникальный ID |
| `source_text` | TEXT | NOT NULL | Исходный текст вакансии |
| `content_hash` | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | SHA256 нормализованного текста |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Время создания |

#### ai_result

Универсальный кеш результатов LLM операций.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Уникальный ID |
| `operation` | VARCHAR(50) | NOT NULL | Тип операции: `parse_resume`, `parse_vacancy`, `analyze_match`, `adapt_resume`, `generate_cover_letter` |
| `input_hash` | VARCHAR(64) | NOT NULL, INDEX | SHA256 входных данных |
| `output_json` | JSONB | NOT NULL | Результат от LLM |
| `model` | VARCHAR(100) | NULL | Модель LLM |
| `provider` | VARCHAR(50) | NULL | Провайдер (`deepseek`, `groq`) |
| `error` | TEXT | NULL | Текст ошибки (если была) |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Время создания |

**Unique constraint:** `(operation, input_hash)`

#### analysis_link

Связывает резюме, вакансию и результат анализа.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Уникальный ID |
| `resume_id` | UUID | FK → resume_raw.id, NOT NULL, INDEX | Ссылка на резюме |
| `vacancy_id` | UUID | FK → vacancy_raw.id, NOT NULL, INDEX | Ссылка на вакансию |
| `analysis_result_id` | UUID | FK → ai_result.id, NOT NULL, INDEX | Ссылка на результат анализа |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Время создания |

### Stage 2: Version & Ideal Tables

#### resume_version

История версий адаптированных резюме.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Уникальный ID версии |
| `resume_id` | UUID | FK → resume_raw.id, NOT NULL, INDEX | Базовое резюме |
| `vacancy_id` | UUID | FK → vacancy_raw.id, NOT NULL, INDEX | Целевая вакансия |
| `parent_version_id` | UUID | FK → resume_version.id, NULL, INDEX | Родительская версия (для цепочки) |
| `text` | TEXT | NOT NULL | Полный текст адаптированного резюме |
| `change_log` | JSONB | NOT NULL | Список изменений [{checkbox_id, what_changed, where, ...}] |
| `selected_checkbox_ids` | JSONB | NOT NULL | IDs выбранных улучшений |
| `safety_notes` | JSONB | NOT NULL | Предупреждения от LLM |
| `analysis_id` | UUID | FK → ai_result.id, NULL | Ссылка на анализ |
| `provider` | VARCHAR(50) | NULL | Провайдер LLM |
| `model` | VARCHAR(100) | NULL | Модель LLM |
| `prompt_version` | VARCHAR(50) | NULL | Версия промпта |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Время создания |

#### ideal_resume

Сгенерированные идеальные резюме для вакансий.

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | UUID | PK | Уникальный ID |
| `vacancy_id` | UUID | FK → vacancy_raw.id, NOT NULL, INDEX | Вакансия |
| `vacancy_hash` | VARCHAR(64) | NOT NULL, INDEX | SHA256 текста вакансии |
| `text` | TEXT | NOT NULL | Полный текст идеального резюме |
| `generation_metadata` | JSONB | NOT NULL | Метаданные: keywords_used, structure, assumptions |
| `options` | JSONB | NOT NULL | Опции генерации: language, template, seniority |
| `input_hash` | VARCHAR(64) | UNIQUE, NOT NULL, INDEX | Хэш для кеширования |
| `provider` | VARCHAR(50) | NULL | Провайдер LLM |
| `model` | VARCHAR(100) | NULL | Модель LLM |
| `created_at` | TIMESTAMP | NOT NULL, DEFAULT now() | Время создания |

## Indexes

| Table | Index | Columns | Type |
|-------|-------|---------|------|
| resume_raw | ix_resume_raw_content_hash | content_hash | UNIQUE |
| vacancy_raw | ix_vacancy_raw_content_hash | content_hash | UNIQUE |
| ai_result | ix_ai_result_input_hash | input_hash | BTREE |
| ai_result | ix_ai_result_operation_input_hash | operation, input_hash | UNIQUE |
| analysis_link | ix_analysis_link_resume_id | resume_id | BTREE |
| analysis_link | ix_analysis_link_vacancy_id | vacancy_id | BTREE |
| analysis_link | ix_analysis_link_analysis_result_id | analysis_result_id | BTREE |
| resume_version | ix_resume_version_resume_id | resume_id | BTREE |
| resume_version | ix_resume_version_vacancy_id | vacancy_id | BTREE |
| resume_version | ix_resume_version_parent_version_id | parent_version_id | BTREE |
| ideal_resume | ix_ideal_resume_vacancy_id | vacancy_id | BTREE |
| ideal_resume | ix_ideal_resume_vacancy_hash | vacancy_hash | BTREE |
| ideal_resume | ix_ideal_resume_input_hash | input_hash | UNIQUE |

## Relationships

### Stage 1

```
resume_raw (1) ←───── (N) analysis_link (N) ─────→ (1) vacancy_raw
                              │
                              │ (N)
                              ▼
                         (1) ai_result
```

- `analysis_link.resume_id` → `resume_raw.id` (ON DELETE CASCADE)
- `analysis_link.vacancy_id` → `vacancy_raw.id` (ON DELETE CASCADE)
- `analysis_link.analysis_result_id` → `ai_result.id` (ON DELETE CASCADE)

### Stage 2

```
resume_raw (1) ←───── (N) resume_version (N) ─────→ (1) vacancy_raw
      │                        │
      │                        ├── parent_version_id → resume_version.id (self-ref)
      │                        │
      │                        └── analysis_id → ai_result.id
      │
      └───────────────────────────────────────────────→ ideal_resume (N) ───→ (1) vacancy_raw
```

- `resume_version.resume_id` → `resume_raw.id` (ON DELETE CASCADE)
- `resume_version.vacancy_id` → `vacancy_raw.id` (ON DELETE CASCADE)
- `resume_version.parent_version_id` → `resume_version.id` (ON DELETE SET NULL)
- `resume_version.analysis_id` → `ai_result.id` (ON DELETE SET NULL)
- `ideal_resume.vacancy_id` → `vacancy_raw.id` (ON DELETE CASCADE)

## Hash Logic

### Text Normalization

```python
def normalize_text(text: str) -> str:
    text = text.strip()
    text = text.replace("\t", " ")
    text = re.sub(r" +", " ", text)  # collapse spaces
    text = re.sub(r"\n\s*\n+", "\n\n", text)  # collapse newlines
    lines = [line.strip() for line in text.split("\n")]
    return "\n".join(lines)
```

### Hash Computation

```python
def compute_hash(text: str) -> str:
    normalized = normalize_text(text)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
```

### Match Hash

Для `analyze_match` хэш вычисляется от конкатенации JSON:

```python
combined = json.dumps(parsed_resume, sort_keys=True) + json.dumps(parsed_vacancy, sort_keys=True)
hash = hashlib.sha256(combined.encode("utf-8")).hexdigest()
```

## JSONB Structures

### ai_result.output_json для parse_resume

```json
{
  "personal_info": {...},
  "summary": "...",
  "skills": [...],
  "work_experience": [...],
  "education": [...],
  "certifications": [...],
  "languages": [...],
  "raw_sections": {...}
}
```

### ai_result.output_json для parse_vacancy

```json
{
  "job_title": "...",
  "company": "...",
  "required_skills": [...],
  "preferred_skills": [...],
  "experience_requirements": {...},
  "responsibilities": [...],
  "ats_keywords": [...]
}
```

### ai_result.output_json для analyze_match

```json
{
  "score": 75,
  "score_breakdown": {...},
  "matched_required_skills": [...],
  "missing_required_skills": [...],
  "gaps": [...],
  "checkbox_options": [...]
}
```
