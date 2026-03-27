"""Integration layer errors (HTTP 502 / 503)."""

from .base import AppError


class AIProviderError(AppError):
    """AI provider call failed (HTTP 502)."""

    status_code: int = 502

    def __init__(self, message: str = "AI provider error") -> None:
        super().__init__(message)


class ScraperError(AppError):
    """Web scraper failed to fetch or parse a URL."""

    def __init__(
        self, message: str = "Failed to fetch URL", *, status_code: int = 502
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
