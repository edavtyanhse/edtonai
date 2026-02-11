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
    ai_provider: str = "deepseek"
    deepseek_api_key: str
    deepseek_base_url: str
    ai_model: str
    ai_timeout_seconds: int
    ai_max_retries: int
    ai_temperature: float
    ai_max_tokens: int

    # Logging
    log_level: str

    # Supabase Auth
    supabase_jwt_secret: str = ""  # JWT secret for token verification

    # Feedback Collection Feature Flag
    # Set to False to disable feedback collection entirely
    # To remove feature: set to False and delete feedback-related files
    feedback_collection_enabled: bool = True


settings = Settings()
