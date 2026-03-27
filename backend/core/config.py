"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта (edtonai/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

# Text limits for frontend
MAX_RESUME_CHARS = 15000
MAX_VACANCY_CHARS = 10000


class Settings(BaseSettings):
    """All settings for Stage 1 backend.

    All values MUST be provided via .env file.
    No defaults - explicit configuration required.
    """

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database (separate credentials)
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: int
    postgres_db: str

    @computed_field
    @property
    def database_url(self) -> str:
        """Build DATABASE_URL from separate credentials."""
        # Allow direct override if set (e.g. for Supabase with special flags)
        if hasattr(self, "DATABASE_URL") and self.DATABASE_URL:
            return self.DATABASE_URL

        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # AI provider
    ai_provider: str = (
        "deepseek"  # Deprecated, kept for backward compatibility if needed
    )

    # AI Configuration
    ai_provider_parsing: str = "groq"
    ai_provider_reasoning: str = "deepseek"

    # DeepSeek
    deepseek_api_key: str | None = None
    deepseek_base_url: str = "https://api.deepseek.com/v1"

    # Groq
    groq_api_key: str | None = None
    groq_model_parsing: str = "llama-3.1-8b-instant"
    groq_model_reasoning: str = "llama-3.3-70b-versatile"

    # General AI config
    # Backward-compatible model name (used by DeepSeekProvider and for metadata storage).
    ai_model: str = "deepseek-reasoner"
    ai_timeout_seconds: int = 180
    ai_max_retries: int = 3
    ai_temperature: float = 0.0
    ai_max_tokens: int = 4096

    # Logging
    log_level: str

    # JWT Authentication
    jwt_secret_key: str = "change-me-in-production"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30

    # SMTP (email sending)
    smtp_host: str = "smtp.yandex.ru"
    smtp_port: int = 465
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_from_email: str = ""

    # Frontend URL (for email verification links)
    frontend_url: str = "http://localhost:3000"

    # Backend URL (for OAuth redirect_uri construction)
    backend_url: str = "http://localhost:8000"

    # OAuth — Google
    google_oauth_client_id: str = ""
    google_oauth_client_secret: str = ""

    # OAuth — VK
    vk_oauth_client_id: str = ""
    vk_oauth_client_secret: str = ""

    # OAuth — Yandex
    yandex_oauth_client_id: str = ""
    yandex_oauth_client_secret: str = ""

    # Feedback Collection Feature Flag
    # Set to False to disable feedback collection entirely
    # To remove feature: set to False and delete feedback-related files
    feedback_collection_enabled: bool = True

    # Database bootstrap
    # Disabled by default so production/Cloud Run startup does not block on DDL.
    db_auto_create: bool = False


settings = Settings()
