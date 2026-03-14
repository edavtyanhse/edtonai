# Backend Documentation

Техническая документация backend-сервиса адаптации резюме.

## 📚 Содержание

| Раздел | Описание |
|--------|----------|
| [API Specification](api/README.md) | Спецификации REST API endpoints |
| [Architecture](architecture/README.md) | Архитектура: DI-контейнер, слои, Protocol-интерфейсы |
| [DB Schema](database/README.md) | PostgreSQL, SQLAlchemy, RLS |
| [AI Integration](ai/README.md) | DeepSeek / Groq LLM, промпты, валидация |
| [Configuration](configuration/README.md) | Переменные окружения |
| [Services](services/README.md) | Бизнес-логика, CachedAIService |

---

## 🛠️ Стек технологий

- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Database:** PostgreSQL 16 (Managed by **Supabase**)
- **ORM:** SQLAlchemy 2.0 (async) + AsyncPG
- **DI:** dependency-injector 4.48 (DeclarativeContainer)
- **AI:** DeepSeek API (reasoning) + Groq API (parsing)
- **Auth:** JWT (Supabase Auth tokens, JWKS)
- **Deployment:** Google Cloud Run

---

## 🚀 Быстрый старт

### Требования
- Python 3.11+
- PostgreSQL (или Supabase проект)
- API Key от DeepSeek и/или Groq

### Локальный запуск

1. **Клонирование и venv:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Настройка окружения:**
   Создай `.env` (или используй системные переменные):
   ```env
   # Database (Supabase Transaction Pooler recommended)
   POSTGRES_USER=postgres.your-project
   POSTGRES_PASSWORD=your-db-password
   POSTGRES_HOST=aws-0-us-east-1.pooler.supabase.com
   POSTGRES_PORT=6543
   POSTGRES_DB=postgres

   # AI
   DEEPSEEK_API_KEY=sk-your-key
   GROQ_API_KEY=gsk_your-key

   # Auth
   SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-settings
   SUPABASE_URL=https://xxx.supabase.co

   # Logging
   LOG_LEVEL=INFO
   ```

3. **Запуск:**
   ```bash
   python main.py
   # API будет доступно на http://localhost:8000
   # Swagger UI: http://localhost:8000/docs
   ```

---

## 🔐 Аутентификация и Безопасность

Сервис не занимается выпуском токенов (это делает Frontend через Supabase Auth).
Backend занимается **валидацией** JWT токенов.

1. **JWKS + JWT Secret:** Токены проверяются через JWKS (`supabase_url + /auth/v1/.well-known/jwks.json`), с fallback на `SUPABASE_JWT_SECRET`.
2. **User Identification:** Из токена извлекается `sub` (UUID пользователя), который используется для фильтрации данных.
3. **RLS:** Фильтрация по `user_id` реализована в репозиториях.

---

## ☁️ Деплой (Google Cloud Run)

Сервис упаковывается в Docker контейнер и деплоится в Cloud Run.

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
# ... установка зависимостей ...
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🏗️ Структура проекта

```
backend/
├── containers.py           # Composition Root (DI-контейнер)
├── main.py                 # Entry point: создание app + wiring + lifespan
│
├── core/
│   ├── auth.py             # JWT verification (JWKS + secret fallback)
│   ├── config.py           # Settings (Pydantic BaseSettings)
│   └── logging.py          # Structured logging setup
│
├── errors/                 # Таксономия ошибок
│   ├── base.py             # AppError базовый класс
│   ├── business.py         # ResumeNotFoundError, VacancyNotFoundError, ...
│   ├── integration.py      # AIProviderError, ScraperError
│   └── handlers.py         # Глобальные FastAPI exception handlers
│
├── integration/            # Внешние системы
│   ├── ai/
│   │   ├── base.py         # AIProvider ABC
│   │   ├── deepseek.py     # DeepSeek (reasoning)
│   │   ├── groq.py         # Groq (parsing)
│   │   ├── errors.py       # AIError, AIRequestError, AIResponseFormatError
│   │   └── prompts.py      # Все LLM-промпты
│   └── scraper/
│       └── scraper.py      # WebScraper (hh.ru API + generic HTML)
│
├── domain/                 # Внутренние DTO (dataclasses)
│   ├── mappers.py          # ORM ↔ dict маппинг (get_/set_parsed_data)
│   ├── resume.py           # ResumeParseResult
│   ├── vacancy.py          # VacancyParseResult
│   ├── match.py            # MatchAnalysisResult
│   ├── adapt.py            # AdaptResumeResult
│   ├── ideal.py            # IdealResumeResult
│   ├── cover_letter.py     # CoverLetterResult
│   └── analysis.py         # FullAnalysisResult
│
├── api/
│   ├── dependencies.py     # @inject — DI из контейнера
│   └── v1/
│       ├── health.py       # GET /health, /v1/health, /v1/limits
│       ├── resumes.py      # POST /v1/resumes/parse, GET, PATCH
│       ├── vacancies.py    # POST /v1/vacancies/parse, GET, PATCH
│       ├── match.py        # POST /v1/match/analyze
│       ├── adapt.py        # POST /v1/resumes/adapt
│       ├── ideal.py        # POST /v1/resumes/ideal
│       ├── cover_letter.py # POST /v1/cover-letter
│       ├── versions.py     # POST/GET /v1/versions
│       └── feedback.py     # POST /v1/feedback
│
├── schemas/                # Pydantic-схемы (API контракт)
│   ├── __init__.py         # Фасад: реэкспорт всех схем
│   ├── common.py           # ChangeLogEntry, Options, ...
│   ├── requests/           # Request-схемы
│   └── responses/          # Response-схемы
│
├── services/               # Бизнес-логика
│   ├── interfaces.py       # Protocol-классы (IResumeService, ...)
│   ├── base.py             # CachedAIService (базовый класс)
│   ├── resume.py
│   ├── vacancy.py
│   ├── match.py
│   ├── orchestrator.py
│   ├── adapt.py
│   ├── ideal.py
│   ├── cover_letter.py
│   └── utils.py
│
├── repositories/           # Persistence layer
│   ├── interfaces.py       # Protocol-классы (IResumeRepository, ...)
│   ├── resume.py
│   ├── vacancy.py
│   ├── ai_result.py
│   ├── analysis.py
│   ├── resume_version.py
│   ├── ideal_resume.py
│   ├── user_version.py
│   └── feedback.py
│
├── models/                 # ORM-маппинги (чистые, без бизнес-логики)
│
├── db/
│   ├── base.py
│   ├── session.py
│   └── migrations/
│
└── tests/
    ├── conftest.py         # container.override() fixtures
    ├── unit/               # Тесты сервисов с мок-зависимостями
    └── integration/        # Тесты API с тестовой БД
```

## Ключевые архитектурные решения

| Решение | Описание |
|---------|----------|
| **DI-контейнер** | `containers.py` — единый Composition Root, все зависимости собираются в одном месте |
| **Protocol-интерфейсы** | `services/interfaces.py`, `repositories/interfaces.py` — сервисы зависят от абстракций, не от конкретных классов |
| **CachedAIService** | Базовый класс для сервисов с AI — устраняет дублирование кеширования |
| **Таксономия ошибок** | `errors/` — типизированные ошибки + глобальные handlers, без try/except в эндпоинтах |
| **Hybrid AI** | Groq (быстрый, для парсинга) + DeepSeek (умный, для анализа) |

## Переменные окружения (Полный список)

| Переменная | Описание |
|------------|----------|
| `DEEPSEEK_API_KEY` | Ключ API DeepSeek |
| `GROQ_API_KEY` | Ключ API Groq |
| `SUPABASE_JWT_SECRET` | Секрет для проверки JWT (из Supabase Settings > API) |
| `SUPABASE_URL` | URL Supabase проекта (для JWKS) |
| `POSTGRES_USER` | Пользователь БД |
| `POSTGRES_PASSWORD` | Пароль БД |
| `POSTGRES_HOST` | Хост БД |
| `POSTGRES_PORT` | Порт БД (обычно 5432 или 6543) |
| `POSTGRES_DB` | Имя БД |
| `LOG_LEVEL` | Уровень логирования (DEBUG, INFO, WARNING, ERROR) |
| `AI_PROVIDER_PARSING` | AI-провайдер для парсинга (groq / deepseek) |
| `AI_PROVIDER_REASONING` | AI-провайдер для анализа (deepseek / groq) |
| `FEEDBACK_COLLECTION_ENABLED` | Включить/выключить сбор фидбека (true/false) |
