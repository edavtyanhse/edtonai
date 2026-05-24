# Configuration

Документация по конфигурации приложения.

## Overview

Приложение использует **Pydantic Settings** для управления конфигурацией:

- Все настройки читаются из `.env` файла
- Типизация и валидация значений
- Computed properties для составных значений (database_url)
- DI-контейнер создаёт `Settings` как `Singleton`

## Settings Class

### Файл

`backend/core/config.py`

### Структура

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    postgres_db: str

    @computed_field
    @property
    def database_url(self) -> str: ...

    # AI provider selection
    ai_provider_parsing: str = "groq"
    ai_provider_reasoning: str = "deepseek"

    # DeepSeek
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Groq
    groq_api_key: str | None = None
    groq_model_parsing: str = "llama-3.1-8b-instant"
    groq_model_reasoning: str = "llama-3.3-70b-versatile"

    # General AI
    ai_model: str = "deepseek-reasoner"
    ai_timeout_seconds: int = 180
    ai_max_retries: int = 3
    ai_temperature: float = 0.0
    ai_max_tokens: int = 4096

    # Logging
    log_level: str

    # Supabase Auth
    supabase_jwt_secret: str = ""
    supabase_url: str = ""

    # Feature flags
    feedback_collection_enabled: bool = True
```

### Использование в DI-контейнере

`Settings` создаётся как `Singleton` в контейнере и инжектируется во все сервисы:

```python
# containers.py
class Container(DeclarativeContainer):
    config = providers.Singleton(Settings)

    resume_service = providers.Factory(
        ResumeService,
        settings=config,  # ← Settings из контейнера
        ...
    )
```

> **Примечание:** Глобальный `settings = Settings()` в `config.py` сохранён для обратной совместимости инфраструктурного кода (`auth.py`, `logging.py`, `db/session.py`). Сервисы **не** обращаются к нему напрямую — получают Settings через конструктор.

## Environment Variables

### Required Variables

| Variable | Type | Description |
|----------|------|-------------|
| `POSTGRES_USER` | str | PostgreSQL username |
| `POSTGRES_PASSWORD` | str | PostgreSQL password |
| `POSTGRES_HOST` | str | Database host |
| `POSTGRES_PORT` | int | Database port |
| `POSTGRES_DB` | str | Database name |
| `LOG_LEVEL` | str | Logging level (DEBUG, INFO, WARNING, ERROR) |

### AI Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DEEPSEEK_API_KEY` | str | None | DeepSeek API key |
| `DEEPSEEK_BASE_URL` | str | `https://api.deepseek.com/v1` | DeepSeek API base URL |
| `GROQ_API_KEY` | str | None | Groq API key |
| `GROQ_MODEL_PARSING` | str | `llama-3.1-8b-instant` | Groq model for parsing |
| `GROQ_MODEL_REASONING` | str | `llama-3.3-70b-versatile` | Groq model for reasoning |
| `AI_PROVIDER_PARSING` | str | `groq` | AI provider for parsing tasks |
| `AI_PROVIDER_REASONING` | str | `deepseek` | AI provider for reasoning tasks |
| `AI_MODEL` | str | `deepseek-reasoner` | Default model name (metadata) |
| `AI_TIMEOUT_SECONDS` | int | `180` | HTTP timeout |
| `AI_MAX_RETRIES` | int | `3` | Retry count on network errors |
| `AI_TEMPERATURE` | float | `0.0` | LLM temperature |
| `AI_MAX_TOKENS` | int | `4096` | Max output tokens |
| `AI_MONTHLY_FREE_QUOTA` | int | `1000000` | Temporary pre-commercial monthly AI quota for free entitlement gates |
| `AI_MONTHLY_TRIAL_QUOTA` | int | `100` | Default monthly AI quota for future trial entitlement gates |

### Security, Scraper And Billing Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `AUTH_RATE_LIMIT_PER_MINUTE` | int | `20` | Auth route rate limit |
| `AI_RATE_LIMIT_PER_MINUTE` | int | `120` | AI-heavy route rate limit |
| `SCRAPER_RATE_LIMIT_PER_MINUTE` | int | `30` | Vacancy URL scraping route rate limit |
| `TRUSTED_PROXY_IPS` | str | `""` | Comma-separated proxy IPs whose `X-Forwarded-For` may be trusted |
| `SCRAPER_ALLOWED_HOSTS` | str | `hh.ru,hh.kz,headhunter.ru,headhunter.kz` | Comma-separated allowlist for user-submitted vacancy URLs |
| `SCRAPER_TIMEOUT_SECONDS` | float | `15` | HTTP timeout for scraper requests |
| `SCRAPER_MAX_HTML_BYTES` | int | `1000000` | Max downloaded HTML/text response size |
| `SCRAPER_MAX_REDIRECTS` | int | `5` | Max validated redirects |
| `PAYMENT_PROVIDER` | str | `disabled` | Payment provider selector; currently `disabled` or `tbank` |
| `BILLING_TEMPORARY_HIGH_FREE_QUOTA_ENABLED` | bool | `false` | Required explicit production opt-in when temporary free quota is very high |
| `PAYMENT_WEBHOOK_REPLAY_TOLERANCE_SECONDS` | int | `300` | Future webhook replay window |
| `TBANK_TERMINAL_KEY` | str | `""` | T-Bank terminal identifier, backend-side |
| `TBANK_PUBLIC_KEY` | str | `""` | Optional T-Bank public identifier/key |
| `TBANK_PASSWORD` | secret | `None` | T-Bank backend secret; never expose as `VITE_*` |
| `TBANK_WEBHOOK_SECRET` | secret | `None` | Future webhook validation secret |

### Auth & Feature Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `SUPABASE_JWT_SECRET` | str | `""` | JWT secret for token verification |
| `SUPABASE_URL` | str | `""` | Supabase project URL (for JWKS endpoint) |
| `FEEDBACK_COLLECTION_ENABLED` | bool | `true` | Enable/disable feedback collection |

## Database URL

URL формируется динамически из отдельных переменных:

```python
@computed_field
@property
def database_url(self) -> str:
    return (
        f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
        f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
    )
```

### Пример

```env
POSTGRES_USER=appuser
POSTGRES_PASSWORD=secret123
POSTGRES_DB=resume_adapter
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

→ `postgresql+asyncpg://appuser:secret123@db:5432/resume_adapter`

## Files

### .env (development)

```env
# ============================================
# DATABASE
# ============================================
POSTGRES_USER=resume_user
POSTGRES_PASSWORD=changeme
POSTGRES_DB=resume_adapter_db
POSTGRES_HOST=db
POSTGRES_PORT=5432

# ============================================
# AI PROVIDER
# ============================================
DEEPSEEK_API_KEY=sk-your-key
GROQ_API_KEY=gsk_your-key

AI_PROVIDER_PARSING=groq
AI_PROVIDER_REASONING=deepseek

AI_TIMEOUT_SECONDS=180
AI_MAX_RETRIES=3
AI_TEMPERATURE=0.0
AI_MAX_TOKENS=4096

# ============================================
# AUTH
# ============================================
SUPABASE_JWT_SECRET=your-jwt-secret
SUPABASE_URL=https://xxx.supabase.co

# ============================================
# LOGGING
# ============================================
LOG_LEVEL=INFO
```

### Docker vs Local

| Environment | `POSTGRES_HOST` |
|-------------|-----------------|
| Docker Compose | `db` (service name) |
| Local development | `localhost` |

## Adding New Settings

1. Добавьте переменную в `.env`
2. Добавьте поле в `Settings` class (`backend/core/config.py`)
3. Если нужно в сервисах — `Settings` уже инжектируется через контейнер
4. Для инфраструктурного кода — доступен через глобальный `settings`
