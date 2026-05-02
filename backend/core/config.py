"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта (edtonai/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

DEFAULT_MAX_RESUME_CHARS = 15000
DEFAULT_MAX_VACANCY_CHARS = 10000
DEVELOPMENT_JWT_SECRET = "development-only-insecure-secret-change-me"


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

    # HuggingFace Inference API
    hf_token: str | None = None
    hf_model_parsing: str = "edmon03/edtonai-generator"
    hf_model_reasoning: str = "edmon03/edtonai-generator"
    # Custom inference endpoint URL (e.g. Cloud Run GPU, HF Dedicated Endpoint).
    # If empty — uses HF Serverless router (free, public models only).
    hf_endpoint_url: str = ""

    # General AI config
    # Backward-compatible model name (used by DeepSeekProvider and for metadata storage).
    ai_model: str = "deepseek-reasoner"
    ai_timeout_seconds: int = 180
    ai_max_retries: int = 3
    ai_temperature: float = 0.0
    ai_max_tokens: int = 4096

    # Logging
    log_level: str

    # Runtime environment
    app_env: str = "development"

    # JWT Authentication
    jwt_secret_key: str = DEVELOPMENT_JWT_SECRET
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 30
    refresh_cookie_path: str = "/"

    # Public input limits
    max_resume_chars: int = DEFAULT_MAX_RESUME_CHARS
    max_vacancy_chars: int = DEFAULT_MAX_VACANCY_CHARS

    # Basic abuse protection. Production can tune these via env.
    auth_rate_limit_per_minute: int = 20
    ai_rate_limit_per_minute: int = 120
    scraper_rate_limit_per_minute: int = 30

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

    # OAuth — Yandex
    yandex_oauth_client_id: str = ""
    yandex_oauth_client_secret: str = ""

    # Semantic Scorer (cross-encoder for resume-vacancy matching)
    scorer_model_path: str = "edmon03/edtonai-scorer"

    # Feedback Collection Feature Flag
    # Set to False to disable feedback collection entirely
    # To remove feature: set to False and delete feedback-related files
    feedback_collection_enabled: bool = True

    # Database bootstrap
    # Disabled by default so production/Cloud Run startup does not block on DDL.
    db_auto_create: bool = False

    @model_validator(mode="after")
    def validate_security_defaults(self) -> "Settings":
        """Fail fast when production-like environments use unsafe secrets."""
        env = self.app_env.lower()
        is_production_like = env not in {"dev", "development", "local", "test"}
        weak_jwt_secret = (
            self.jwt_secret_key == DEVELOPMENT_JWT_SECRET
            or len(self.jwt_secret_key) < 32
        )
        if is_production_like and weak_jwt_secret:
            raise ValueError(
                "JWT_SECRET_KEY must be set to a strong non-default value "
                "outside development/test environments"
            )
        return self


settings = Settings()

# Backward-compatible aliases for existing imports and public limits endpoint.
MAX_RESUME_CHARS = settings.max_resume_chars
MAX_VACANCY_CHARS = settings.max_vacancy_chars
