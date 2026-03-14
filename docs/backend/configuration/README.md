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
