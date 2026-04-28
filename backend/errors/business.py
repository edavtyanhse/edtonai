"""Business logic errors (HTTP 4xx)."""

from .base import AppError


class ValidationError(AppError):
    """Input data is invalid (HTTP 400)."""

    status_code: int = 400


class UnprocessableEntityError(AppError):
    """Input data is semantically invalid (HTTP 422)."""

    status_code: int = 422


class NotFoundError(AppError):
    """Requested entity not found (HTTP 404)."""

    status_code: int = 404


class ResumeNotFoundError(NotFoundError):
    """Resume not found."""

    def __init__(self, resume_id: str | None = None) -> None:
        detail = f"Resume not found: {resume_id}" if resume_id else "Resume not found"
        super().__init__(detail)


class VacancyNotFoundError(NotFoundError):
    """Vacancy not found."""

    def __init__(self, vacancy_id: str | None = None) -> None:
        detail = (
            f"Vacancy not found: {vacancy_id}" if vacancy_id else "Vacancy not found"
        )
        super().__init__(detail)


class VersionNotFoundError(NotFoundError):
    """Resume version not found."""

    def __init__(self, version_id: str | None = None) -> None:
        detail = (
            f"Resume version not found: {version_id}"
            if version_id
            else "Resume version not found"
        )
        super().__init__(detail)


class AccessDeniedError(AppError):
    """Access denied — user does not own the resource (HTTP 403)."""

    status_code: int = 403

    def __init__(self, message: str = "Access denied") -> None:
        super().__init__(message)
