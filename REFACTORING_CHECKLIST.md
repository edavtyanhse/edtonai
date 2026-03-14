# 🔧 Чеклист рефакторинга архитектуры EdTon.ai

> Дата создания: 2026-02-28
> Цель: привести проект в соответствие с принципами SOLID, внедрить полноценный DI-контейнер, реструктурировать пакеты по ответственности, устранить архитектурные антипаттерны.

---

## 🔴 Этап 0. Реструктуризация файловой системы (Фундамент)

> ✅ **ЗАВЕРШЁН** — все 7 подэтапов выполнены, ruff 0 errors, health-тесты 3/3 pass.

> Перенос файлов по принципу «пакет по ответственности» (integration, domain, errors).
> Все импорты обновляются сразу. Функциональность не меняется — только расположение.

### 0.1 `integration/` — отделение внешних систем
- [x] Создать `backend/integration/__init__.py`
- [x] Создать `backend/integration/ai/__init__.py`
- [x] Перенести `backend/ai/base.py` → `backend/integration/ai/base.py`
- [x] Перенести `backend/ai/deepseek.py` → `backend/integration/ai/deepseek.py`
- [x] Перенести `backend/ai/groq.py` → `backend/integration/ai/groq.py`
- [x] Перенести `backend/ai/errors.py` → `backend/integration/ai/errors.py`
- [x] Перенести `backend/ai/factory.py` → `backend/integration/ai/factory.py` (временно, будет удалён на этапе 2)
- [x] Перенести `backend/prompts.py` → `backend/integration/ai/prompts.py`
- [x] Создать `backend/integration/scraper/__init__.py`
- [x] Перенести `backend/services/scraper.py` → `backend/integration/scraper/scraper.py`
- [x] Удалить пустой `backend/ai/` после переноса
- [x] Обновить все импорты по проекту (`backend.ai.` → `backend.integration.ai.`, `backend.prompts` → `backend.integration.ai.prompts`)

### 0.2 `errors/` — таксономия ошибок
- [x] Создать `backend/errors/__init__.py`
- [x] Создать `backend/errors/base.py` — `AppError` базовый класс
- [x] Создать `backend/errors/business.py` — `ResumeNotFoundError`, `VacancyNotFoundError`, `VersionNotFoundError`, `AccessDeniedError`
- [x] Создать `backend/errors/integration.py` — реэкспорт `AIError`, `AIRequestError`, `AIResponseFormatError`, `ScraperError`
- [x] Создать `backend/errors/handlers.py` — FastAPI exception handlers
- [x] Заменить голые `ValueError` / `raise HTTPException` в сервисах на типизированные ошибки
- [x] Зарегистрировать обработчики в `main.py`
- [x] Убрать try/except из эндпоинтов

### 0.3 `domain/` — внутренние DTO
- [x] Создать `backend/domain/__init__.py`
- [x] Создать `backend/domain/resume.py` — `ResumeParseResult` (из `services/resume.py`)
- [x] Создать `backend/domain/vacancy.py` — `VacancyParseResult` (из `services/vacancy.py`)
- [x] Создать `backend/domain/match.py` — `MatchAnalysisResult` (из `services/match.py`)
- [x] Создать `backend/domain/adapt.py` — `SelectedImprovement`, `AdaptResumeResult` (из `services/adapt.py`)
- [x] Создать `backend/domain/ideal.py` — `IdealResumeResult` (из `services/ideal.py`)
- [x] Создать `backend/domain/cover_letter.py` — `CoverLetterResult` (из `services/cover_letter.py`)
- [x] Создать `backend/domain/analysis.py` — `FullAnalysisResult` (из `services/orchestrator.py`)
- [x] Удалить dataclass-определения из сервисов, импортировать из `domain/`

### 0.4 `schemas/` — разделение request / response
- [x] Создать `backend/schemas/requests/__init__.py`
- [x] Перенести request-схемы: `ResumeParseRequest`, `VacancyParseRequest`, `MatchAnalyzeRequest`, `AdaptResumeRequest`, `IdealResumeRequest`, `CoverLetterRequest`, `VersionCreateRequest`, `ResumePatchRequest`, `VacancyPatchRequest`
- [x] Создать `backend/schemas/responses/__init__.py`
- [x] Перенести response-схемы: `ResumeParseResponse`, `VacancyParseResponse`, `MatchAnalyzeResponse`, `AdaptResumeResponse`, `IdealResumeResponse`, `CoverLetterResponse`, `VersionDetailResponse`, `VersionListResponse`, `ResumeDetailResponse`, `VacancyDetailResponse`
- [x] Создать `backend/schemas/common.py` — общие схемы (`ChangeLogEntry`, `AdaptResumeOptions`, `IdealResumeOptions`, и т.д.)
- [x] Обновить `backend/schemas/__init__.py` — реэкспорт из подпакетов
- [x] Обновить импорты в API-эндпоинтах

### 0.5 Вынести health/limits из `main.py`
- [x] Создать `backend/api/v1/health.py` с эндпоинтами `/health` и `/limits`
- [x] Убрать эндпоинты из `main.py`
- [x] `main.py` содержит только: создание app, middleware, lifespan, include router

### 0.6 `tests/` — разделение unit / integration
- [x] Создать `backend/tests/unit/`
- [x] Создать `backend/tests/integration/`
- [x] Перенести `test_health.py`, `test_api_validation.py` → `integration/`
- [x] Перенести `test_business_flow.py` → `integration/`
- [x] Подготовить структуру для unit-тестов сервисов

### 0.7 `db/migrations/` — объединение
- [x] Перенести `backend/migrations/` → `backend/db/migrations/`
- [x] Обновить пути в скриптах миграции

---

## ✅ Этап 1. DI-контейнер и Dependency Inversion (Критичный)

### 1.1 Установка и настройка `dependency-injector`
- [x] Добавить `dependency-injector>=4.41.0` в `requirements.txt`
- [x] Создать файл `backend/containers.py` — единый Composition Root

### 1.2 Абстракции для репозиториев (Dependency Inversion Principle)
- [x] Создать `backend/repositories/interfaces.py` с Protocol-классами:
  - [x] `IResumeRepository`
  - [x] `IVacancyRepository`
  - [x] `IAIResultRepository`
  - [x] `IAnalysisRepository`
  - [x] `IResumeVersionRepository`
  - [x] `IIdealResumeRepository`
  - [x] `IUserVersionRepository`
  - [x] `IFeedbackRepository`
- [x] Все конкретные репозитории реализуют соответствующий Protocol
- [x] Сервисы зависят от Protocol, а не от конкретного класса

### 1.3 Абстракции для сервисов
- [x] Создать `backend/services/interfaces.py` с Protocol-классами:
  - [x] `IResumeService`
  - [x] `IVacancyService`
  - [x] `IMatchService`
  - [x] `IOrchestratorService`
  - [x] `IAdaptResumeService`
  - [x] `IIdealResumeService`
  - [x] `ICoverLetterService`
- [x] Сервисы, используемые как зависимости в других сервисах (`OrchestratorService` → `ResumeService`, `VacancyService`, `MatchService`), ссылаются на Protocol

### 1.4 Контейнер (`backend/containers.py`)
- [x] `Singleton` provider для `Settings`
- [x] `Resource` provider для `AsyncSession` (DB)
- [x] `Factory` providers для `AIProvider` (parsing / reasoning)
- [x] `Factory` providers для всех 8 репозиториев
- [x] `Factory` providers для всех 7 сервисов с правильным wiring зависимостей
- [x] Wiring контейнера с модулем `backend.api.dependencies`

### 1.5 Рефакторинг конструкторов сервисов
- [x] `ResumeService.__init__` — принимает `IResumeRepository`, `IAIResultRepository`, `AIProvider`, `Settings`
- [x] `VacancyService.__init__` — аналогично
- [x] `MatchService.__init__` — принимает `IAIResultRepository`, `AIProvider`, `Settings`
- [x] `OrchestratorService.__init__` — принимает `IResumeService`, `IVacancyService`, `IMatchService`, `IAnalysisRepository`
- [x] `AdaptResumeService.__init__` — принимает репозитории и сервисы через интерфейсы
- [x] `IdealResumeService.__init__` — аналогично
- [x] `CoverLetterService.__init__` — аналогично

### 1.6 Рефакторинг API dependencies
- [x] Удалить ручные фабрики из `backend/api/dependencies.py`
- [x] Заменить на `@inject` + `Depends(Provide[Container.service])` из `dependency-injector`
- [ ] *(отложено)* Перевести `get_db`/`get_session` в endpoint'ах `vacancies`, `resumes`, `feedback` на провайдер сессии из контейнера

### 1.7 Settings через контейнер
- [ ] *(отложено)* Убрать глобальный `settings = Settings()` из `backend/core/config.py` (оставлен для обратной совместимости)
- [x] Создавать `Settings` внутри контейнера как `Singleton`
- [x] Все 7 сервисов получают settings через инъекцию конструктора

### 1.8 AI Factory → контейнер
- [ ] *(отложено)* Удалить `backend/integration/ai/factory.py` (оставлен для обратной совместимости)
- [x] Провайдеры AI определяются в `containers.py` как `Factory` с helper `_create_ai_provider()`

---

## ✅ Этап 2. Устранение дублирования и улучшения (Важный)

> ✅ **ЗАВЕРШЁН** — CachedAIService base class, ORM cleanup, 12 новых unit-тестов, ruff 0 errors, 22/24 tests pass (2 pre-existing asyncpg).

### 2.1 Базовый класс `CachedAIService`
- [x] Создать `backend/services/base.py` с классом `CachedAIService`
- [x] Вынести общий паттерн кеширования:
  - [x] `_check_cache(input_hash) -> CachedResult | None`
  - [x] `_save_to_cache(input_hash, output_json) -> AIResult`
  - [x] `_call_ai_with_cache(input_hash, prompt) -> (dict, bool)`
  - [x] `_post_process_output(output_json)` — хук для MatchService score clamping
  - [x] `provider_name` / `model_name` — property-хелперы
- [x] Рефакторинг `MatchService` — наследовать `CachedAIService`
- [x] Рефакторинг `ResumeService` — наследовать `CachedAIService`
- [x] Рефакторинг `VacancyService` — наследовать `CachedAIService`
- [x] Рефакторинг `AdaptResumeService` — наследовать `CachedAIService`
- [x] Рефакторинг `CoverLetterService` — наследовать `CachedAIService`
- [x] Рефакторинг `IdealResumeService` — наследовать `CachedAIService` (ai_result_repo=None, свой кеш через ideal_repo)

### 2.2 Убрать бизнес-логику из ORM-моделей
- [x] Создать `backend/domain/mappers.py` — standalone функции `get_/set_resume_parsed_data`, `get_/set_vacancy_parsed_data`
- [x] Перенести `ResumeRaw.set_parsed_data()` / `get_parsed_data()` в маппер
- [x] Перенести `VacancyRaw.set_parsed_data()` / `get_parsed_data()` аналогично
- [x] ORM-модели содержат только маппинг на таблицы, никакой логики
- [x] Обновить все вызовы: сервисы, API-эндпоинты, репозитории

### 2.3 Улучшение тестов
- [x] `test_business_flow.py` уже использует `container.override()` (сделано в Этапе 1)
- [x] `test_api_validation.py` уже использует контейнерные оверрайды (через conftest)
- [x] Добавить unit-тесты для сервисов с мок-репозиториями → `backend/tests/unit/test_services.py` (8 тестов)
- [x] Добавить тест на создание контейнера (smoke test) → `backend/tests/unit/test_container.py` (4 теста)

### 2.4 Мелкие улучшения кода
- [x] `score` clamping в `MatchService` — вынесен в `_clamp_scores()` статический метод + `_SCORE_LIMITS` константу
- [x] `auth.py` — hardcoded JWKS URL → `settings.supabase_url` (добавлено поле в Settings)

---

## 📐 Целевая структура после рефакторинга

```
backend/
├── containers.py                   # Composition Root (DI-контейнер)
├── main.py                         # Только создание app + wiring контейнера
│
├── core/                           # Инфраструктурное ядро
│   ├── config.py                   # Settings (без глобального синглтона)
│   ├── logging.py
│   └── auth.py
│
├── errors/                         # Таксономия ошибок
│   ├── __init__.py
│   ├── base.py                     # AppError базовый класс
│   ├── business.py                 # ResumeNotFoundError, VacancyNotFoundError, ...
│   ├── integration.py              # AIProviderError, ScraperError, ...
│   └── handlers.py                 # FastAPI exception handlers
│
├── integration/                    # Внешние системы (AI, scraper)
│   ├── __init__.py
│   ├── ai/
│   │   ├── __init__.py
│   │   ├── base.py                 # AIProvider ABC
│   │   ├── deepseek.py
│   │   ├── groq.py
│   │   ├── errors.py
│   │   └── prompts.py
│   └── scraper/
│       ├── __init__.py
│       └── scraper.py
│
├── domain/                         # Внутренние DTO (dataclasses)
│   ├── __init__.py
│   ├── mappers.py                  # get_/set_resume_parsed_data, get_/set_vacancy_parsed_data
│   ├── resume.py                   # ResumeParseResult
│   ├── vacancy.py                  # VacancyParseResult
│   ├── match.py                    # MatchAnalysisResult
│   ├── adapt.py                    # SelectedImprovement, AdaptResumeResult
│   ├── ideal.py                    # IdealResumeResult
│   ├── cover_letter.py             # CoverLetterResult
│   └── analysis.py                 # FullAnalysisResult
│
├── api/                            # HTTP-контракты (входные точки)
│   ├── dependencies.py             # @inject из контейнера
│   └── v1/
│       ├── health.py               # health + limits
│       ├── resumes.py
│       ├── vacancies.py
│       ├── match.py
│       ├── adapt.py
│       ├── ideal.py
│       ├── cover_letter.py
│       ├── versions.py
│       └── feedback.py
│
├── schemas/                        # Pydantic-схемы (API контракт)
│   ├── __init__.py                 # Реэкспорт
│   ├── common.py                   # Общие (ChangeLogEntry, Options, ...)
│   ├── requests/
│   │   ├── __init__.py
│   │   ├── resume.py
│   │   ├── vacancy.py
│   │   ├── match.py
│   │   ├── adapt.py
│   │   ├── ideal.py
│   │   ├── cover_letter.py
│   │   └── version.py
│   └── responses/
│       ├── __init__.py
│       ├── resume.py
│       ├── vacancy.py
│       ├── match.py
│       ├── adapt.py
│       ├── ideal.py
│       ├── cover_letter.py
│       └── version.py
│
├── services/                       # Бизнес-логика
│   ├── interfaces.py               # Protocol-классы
│   ├── base.py                     # CachedAIService
│   ├── resume.py
│   ├── vacancy.py
│   ├── match.py
│   ├── orchestrator.py
│   ├── adapt.py
│   ├── ideal.py
│   ├── cover_letter.py
│   └── utils.py
│
├── repositories/                   # Persistence layer
│   ├── interfaces.py               # Protocol-классы
│   ├── resume.py
│   ├── vacancy.py
│   ├── ai_result.py
│   ├── analysis.py
│   ├── resume_version.py
│   ├── ideal_resume.py
│   ├── user_version.py
│   └── feedback.py
│
├── models/                         # ORM-маппинги (чистые, без логики)
│   ├── resume.py
│   ├── vacancy.py
│   ├── ai_result.py
│   └── ...
│
├── db/
│   ├── base.py
│   ├── session.py
│   └── migrations/
│
└── tests/
    ├── conftest.py                 # container.override()
    ├── unit/                       # Тесты сервисов с мок-зависимостями
    └── integration/                # Тесты API с тестовой БД
```

---

## ✅ Критерии завершения

- [x] Файловая структура соответствует целевой схеме выше
- [x] `integration/` содержит все внешние вызовы (AI, scraper), `services/` — только бизнес-логику
- [x] `errors/` — единая таксономия ошибок, эндпоинты не содержат try/except
  > ℹ️ Исключения: `health.py` (инфраструктурный DB-чек), `feedback.py` (JWT-декод с fallback) — не бизнес-логика, а инфраструктурный код
- [x] `domain/` — внутренние DTO отделены от сервисов (+ `mappers.py` для ORM ↔ dict)
- [x] `schemas/requests/` и `schemas/responses/` разделены
- [x] Ни один сервис не создаёт свои зависимости через `import` + вызов конструктора в `__init__`
- [x] Все зависимости сервисов типизированы через `Protocol` / `ABC`
- [x] Граф зависимостей собирается в одном месте (`containers.py`)
- [x] Тесты используют `container.override()` — ни одного `unittest.mock.patch` на пути импорта
- [x] Глобальный `settings` не используется напрямую ни в одном сервисе
- [x] Дублирование кеширования устранено через `CachedAIService`
- [x] `main.py` содержит только bootstrap — без эндпоинтов

### Остающиеся отложенные задачи (backlog)

- [ ] Убрать глобальный `settings = Settings()` из `config.py` — требует обновления `auth.py`, `logging.py`, `db/session.py`, AI providers
- [ ] Удалить `backend/integration/ai/factory.py` — заменён на `containers.py`, но сохранён для обратной совместимости
- [ ] Перевести `get_db`/`get_session` в endpoint'ах на провайдер сессии из контейнера
