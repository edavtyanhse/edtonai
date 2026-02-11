# Services Layer

Сервисный слой содержит бизнес-логику приложения.

## Обзор сервисов

### Stage 1: Парсинг и анализ

| Service | File | Responsibility |
|---------|------|----------------|
| `ResumeService` | `services/resume.py` | Парсинг и кеширование резюме |
| `VacancyService` | `services/vacancy.py` | Парсинг и кеширование вакансий |
| `MatchService` | `services/match.py` | Анализ соответствия |
| `OrchestratorService` | `services/orchestrator.py` | Координация pipeline |

### Stage 2: Адаптация и генерация

| Service | File | Responsibility |
|---------|------|----------------|
| `AdaptResumeService` | `services/adapt.py` | Адаптация резюме по checkbox_options |
| `IdealResumeService` | `services/ideal.py` | Генерация идеального резюме |
| `CoverLetterService` | `services/cover_letter.py` | Генерация сопроводительного письма |

## Детальные описания

- [ResumeService](resume_service.md)
- [VacancyService](vacancy_service.md)
- [MatchService](match_service.md)
- [OrchestratorService](orchestrator_service.md)
- [AdaptResumeService](adapt_service.md) — Stage 2
- [IdealResumeService](ideal_service.md) — Stage 2
- [CoverLetterService](cover_letter_service.md) — Stage 2
- [Utils](utils.md)

## Общий паттерн

Все сервисы следуют одному паттерну:

```python
class SomeService:
    OPERATION = "operation_name"  # для AIResult
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.some_repo = SomeRepository(session)
        self.ai_result_repo = AIResultRepository(session)
        self.ai_provider = DeepSeekProvider()
        self.logger = logging.getLogger(__name__)
    
    async def process_and_cache(self, input_data: str) -> Result:
        # 1. Compute hash
        content_hash = compute_hash(input_data)
        
        # 2. Get or create raw record
        record = await self.some_repo.get_by_hash(content_hash)
        if record is None:
            record = await self.some_repo.create(input_data, content_hash)
        
        # 3. Check cache
        cached = await self.ai_result_repo.get(self.OPERATION, content_hash)
        if cached:
            return Result(..., cache_hit=True)
        
        # 4. Call LLM
        result_json = await self.ai_provider.generate_json(prompt)
        
        # 5. Save to cache
        await self.ai_result_repo.save(
            operation=self.OPERATION,
            input_hash=content_hash,
            output_json=result_json,
            ...
        )
        
        return Result(..., cache_hit=False)
```

## Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    OrchestratorService                          │
│                                                                 │
│  run_analysis(resume_text, vacancy_text)                        │
│       │                                                         │
│       ├──► ResumeService.parse_and_cache()                      │
│       │         │                                               │
│       │         ├──► ResumeRepository                           │
│       │         ├──► AIResultRepository                         │
│       │         └──► DeepSeekProvider                           │
│       │                                                         │
│       ├──► VacancyService.parse_and_cache()                     │
│       │         │                                               │
│       │         ├──► VacancyRepository                          │
│       │         ├──► AIResultRepository                         │
│       │         └──► DeepSeekProvider                           │
│       │                                                         │
│       ├──► MatchService.analyze_and_cache()                     │
│       │         │                                               │
│       │         ├──► AIResultRepository                         │
│       │         └──► DeepSeekProvider                           │
│       │                                                         │
│       └──► AnalysisRepository.link()                            │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│                    CoverLetterService                           │
│                                                                 │
│  generate_cover_letter(resume_version_id)                        │
│       │                                                         │
│       ├──► ResumeVersionRepository                              │
│       ├──► VacancyRepository                                    │
│       ├──► AIResultRepository                                   │
│       └──► DeepSeekProvider                                     │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Кеширование

### Принцип

1. Входные данные нормализуются
2. Вычисляется SHA256 хэш
3. Проверяется `ai_result` по `(operation, input_hash)`
4. Если найдено — возврат из кеша
5. Если нет — вызов LLM и сохранение

### Преимущества

- **Экономия токенов** — повторные запросы бесплатны
- **Скорость** — кешированный ответ ~10мс vs ~3-5с от LLM
- **Идемпотентность** — одинаковые входы = одинаковые выходы
- **Аналитика** — все результаты сохранены в БД

### Инвалидация

В Stage 1 кеш не инвалидируется. Для нового результата нужно:
- Изменить входной текст (даже пробел)
- Или удалить запись из `ai_result` вручную
