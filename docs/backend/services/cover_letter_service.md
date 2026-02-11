# CoverLetterService

Сервис генерации сопроводительного письма на основе версии резюме, вакансии и анализа соответствия.

## Файл

`backend/services/cover_letter.py`

## Класс

```python
class CoverLetterService:
    OPERATION = "generate_cover_letter"
```

## Зависимости

- `ResumeVersionRepository` — получение версии резюме (текст, vacancy_id, analysis_id)
- `VacancyRepository` — получение исходного текста вакансии
- `AIResultRepository` — кеш LLM-результатов и получение анализа
- `DeepSeekProvider` — вызовы LLM (через `get_ai_provider()`)

## Dataclass результата

```python
@dataclass
class CoverLetterResult:
    cover_letter_id: UUID      # ID записи в ai_result
    resume_version_id: UUID    # ID версии резюме
    vacancy_id: UUID           # ID вакансии
    cover_letter_text: str     # Полный текст письма
    structure: dict[str, str]  # {opening, body, closing}
    key_points_used: list[str] # Навыки и факты из резюме
    alignment_notes: list[str] # Как письмо адресует требования
    cache_hit: bool            # True если из кеша
```

## Методы

### `generate_cover_letter(resume_version_id, options) -> CoverLetterResult`

Генерирует сопроводительное письмо для конкретной версии резюме.

#### Параметры

| Name | Type | Description |
|------|------|-------------|
| `resume_version_id` | UUID | ID версии резюме |
| `options` | dict (optional) | Дополнительные опции (зарезервировано) |

#### Алгоритм

```
generate_cover_letter(resume_version_id, options)
│
├── 1. version_repo.get_by_id(resume_version_id)
│       → resume_version (text, vacancy_id, analysis_id)
│       → ValueError if not found
│
├── 2. vacancy_repo.get_by_id(resume_version.vacancy_id)
│       → vacancy (source_text)
│       → ValueError if not found
│
├── 3. ai_result_repo.get_by_id(resume_version.analysis_id)
│       → analysis_result (output_json = match_analysis)
│       → ValueError if no analysis_id or not found
│
├── 4. _compute_cover_letter_hash(
│       resume_version.text, vacancy.source_text, match_analysis)
│       │
│       ├── json.dumps({operation, resume_text, vacancy_text, match_analysis},
│       │              sort_keys=True)
│       └── sha256(json_string)
│
├── 5. ai_result_repo.get("generate_cover_letter", hash)
│       │
│       ├── Found? → return CoverLetterResult(cache_hit=True)
│       │
│       └── Not found? → continue
│
├── 6. Build prompt
│       │
│       └── COVER_LETTER_PROMPT
│             .replace("{{RESUME_TEXT}}", resume_version.text)
│             .replace("{{VACANCY_TEXT}}", vacancy.source_text)
│             .replace("{{MATCH_ANALYSIS_JSON}}", json.dumps(match_analysis))
│
├── 7. ai_provider.generate_json(prompt, "generate_cover_letter")
│
├── 8. ai_result_repo.save(
│       operation="generate_cover_letter",
│       input_hash=hash,
│       output_json=cover_letter_json,
│       provider=..., model=...
│   )
│
└── 9. return CoverLetterResult(cache_hit=False)
```

## Hash Computation

```python
def _compute_cover_letter_hash(
    self,
    resume_version_text: str,
    vacancy_text: str,
    match_analysis: dict[str, Any],
) -> str:
    data = {
        "operation": self.OPERATION,
        "resume_version_text": resume_version_text,
        "vacancy_text": vacancy_text,
        "match_analysis": match_analysis,
    }
    return hashlib.sha256(
        json.dumps(data, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()
```

**Важно:** Хэш включает `operation` + все три входа. Одинаковые резюме + вакансия + анализ → одинаковый хэш → результат из кеша.

## Prompt

Использует `COVER_LETTER_PROMPT` из `backend/prompts.py`.

### Входные данные для LLM

| Placeholder | Source | Description |
|-------------|--------|-------------|
| `{{RESUME_TEXT}}` | `resume_version.text` | Текст адаптированного резюме |
| `{{VACANCY_TEXT}}` | `vacancy.source_text` | Исходный текст вакансии |
| `{{MATCH_ANALYSIS_JSON}}` | `analysis_result.output_json` | JSON-результат анализа соответствия |

### Критические правила промпта

- Использовать **только** опыт и навыки из текста резюме
- Запрещено придумывать проекты, технологии или достижения
- Обязательно учитывать `required_skills` из вакансии
- Если есть `missing_required_skills` — объяснить смежный опыт
- Письмо должно быть профессиональным и естественным

### Ожидаемый JSON от LLM

```json
{
  "cover_letter_text": "Полный текст сопроводительного письма",
  "structure": {
    "opening": "Вступительный абзац",
    "body": "Основная аргументация",
    "closing": "Заключительный абзац"
  },
  "key_points_used": ["Навык 1", "Факт 2"],
  "alignment_notes": ["Как адресованы требования", "Как обработаны пробелы"]
}
```

## Dependency Injection

```python
# backend/api/dependencies.py
def get_cover_letter_service(
    db: AsyncSession = Depends(get_db),
) -> CoverLetterService:
    return CoverLetterService(db)
```

## Пример использования

```python
cover_letter_service = CoverLetterService(session)

result = await cover_letter_service.generate_cover_letter(
    resume_version_id=UUID("a1b2c3d4-..."),
)

print(result.cover_letter_text)
print(f"Key points: {result.key_points_used}")
print(f"Cache hit: {result.cache_hit}")
```
