"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic import SecretStr, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень проекта (edtonai/)
PROJECT_ROOT = Path(__file__).parent.parent.parent

DEFAULT_MAX_RESUME_CHARS = 15000
DEFAULT_MAX_VACANCY_CHARS = 10000
DEVELOPMENT_JWT_SECRET = "development-only-insecure-secret-change-me"
TEMPORARY_HIGH_FREE_QUOTA_LIMIT = 10_000


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
    trusted_proxy_ips: str = ""
    ai_monthly_free_quota: int = 1_000_000
    ai_monthly_trial_quota: int = 100
    billing_temporary_high_free_quota_enabled: bool = False

    @computed_field
    @property
    def trusted_proxy_ip_set(self) -> set[str]:
        """Proxy IPs whose forwarded client headers may be trusted."""
        return {
            ip.strip()
            for ip in self.trusted_proxy_ips.split(",")
            if ip.strip()
        }

    # Scraper SSRF guard. Empty/unlisted hosts are blocked by default.
    scraper_allowed_hosts: str = "hh.ru,hh.kz,headhunter.ru,headhunter.kz"
    scraper_timeout_seconds: float = 15.0
    scraper_max_html_bytes: int = 1_000_000
    scraper_max_redirects: int = 5
    hh_api_user_agent: str = "EdTonAI/1.0 (contact@edtonai.tech)"

    @computed_field
    @property
    def scraper_allowed_host_set(self) -> set[str]:
        """Normalized host allowlist for user-provided vacancy URLs."""
        return {
            host.strip().lower()
            for host in self.scraper_allowed_hosts.split(",")
            if host.strip()
        }

    # Billing / payment provider selection.
    payment_provider: str = "disabled"
    payment_webhook_replay_tolerance_seconds: int = 300

    # T-Bank internet acquiring. Secrets must stay backend-only.
    tbank_terminal_key: str = ""
    tbank_public_key: str = ""
    tbank_password: SecretStr | None = None
    tbank_webhook_secret: SecretStr | None = None

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
        def has_secret_value(secret: SecretStr | None) -> bool:
            return secret is not None and bool(secret.get_secret_value().strip())

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
        if (
            is_production_like
            and self.ai_monthly_free_quota > TEMPORARY_HIGH_FREE_QUOTA_LIMIT
            and not self.billing_temporary_high_free_quota_enabled
        ):
            raise ValueError(
                "Temporary high AI_MONTHLY_FREE_QUOTA in production requires "
                "BILLING_TEMPORARY_HIGH_FREE_QUOTA_ENABLED=true"
            )
        provider = self.payment_provider.lower()
        if provider not in {"disabled", "tbank"}:
            raise ValueError("PAYMENT_PROVIDER must be one of: disabled, tbank")
        if provider == "tbank" and (
            not self.tbank_terminal_key.strip()
            or not has_secret_value(self.tbank_password)
            or not has_secret_value(self.tbank_webhook_secret)
        ):
            raise ValueError(
                "T-Bank payments require TBANK_TERMINAL_KEY, TBANK_PASSWORD, "
                "and TBANK_WEBHOOK_SECRET"
            )
        if self.scraper_timeout_seconds <= 0:
            raise ValueError("SCRAPER_TIMEOUT_SECONDS must be positive")
        if self.scraper_max_html_bytes <= 0:
            raise ValueError("SCRAPER_MAX_HTML_BYTES must be positive")
        if self.scraper_max_redirects < 0:
            raise ValueError("SCRAPER_MAX_REDIRECTS must be non-negative")
        if (
            not self.hh_api_user_agent.strip()
            or len(self.hh_api_user_agent) > 256
            or any(ord(char) < 32 or ord(char) == 127 for char in self.hh_api_user_agent)
        ):
            raise ValueError(
                "HH_API_USER_AGENT must be non-empty, <=256 chars, "
                "and must not contain control characters"
            )
        if self.payment_webhook_replay_tolerance_seconds <= 0:
            raise ValueError(
                "PAYMENT_WEBHOOK_REPLAY_TOLERANCE_SECONDS must be positive"
            )
        return self


settings = Settings()

# Backward-compatible aliases for existing imports and public limits endpoint.
MAX_RESUME_CHARS = settings.max_resume_chars
MAX_VACANCY_CHARS = settings.max_vacancy_chars
