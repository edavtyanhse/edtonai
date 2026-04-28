"""Application error taxonomy.

All typed exceptions and global FastAPI exception handlers.
"""

from .base import AppError
from .business import (
    AccessDeniedError,
    NotFoundError,
    ResumeNotFoundError,
    UnprocessableEntityError,
    VacancyNotFoundError,
    ValidationError,
    VersionNotFoundError,
)
from .integration import AIProviderError, ScraperError, ServiceUnavailableError

__all__ = [
    "AppError",
    "NotFoundError",
    "ResumeNotFoundError",
    "VacancyNotFoundError",
    "VersionNotFoundError",
    "AccessDeniedError",
    "ValidationError",
    "UnprocessableEntityError",
    "AIProviderError",
    "ScraperError",
    "ServiceUnavailableError",
]
