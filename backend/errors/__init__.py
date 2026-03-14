"""Application error taxonomy.

All typed exceptions and global FastAPI exception handlers.
"""

from .base import AppError
from .business import (
    AccessDeniedError,
    NotFoundError,
    ResumeNotFoundError,
    VacancyNotFoundError,
    ValidationError,
    VersionNotFoundError,
)
from .integration import AIProviderError, ScraperError

__all__ = [
    "AppError",
    "NotFoundError",
    "ResumeNotFoundError",
    "VacancyNotFoundError",
    "VersionNotFoundError",
    "AccessDeniedError",
    "ValidationError",
    "AIProviderError",
    "ScraperError",
]
