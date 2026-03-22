"""Authentication and authorization errors."""

from .base import AppError


class AuthenticationError(AppError):
    """Base authentication error (HTTP 401)."""

    status_code: int = 401


class InvalidCredentialsError(AuthenticationError):
    """Wrong email or password."""

    def __init__(self) -> None:
        super().__init__("Invalid email or password")


class TokenExpiredError(AuthenticationError):
    """Access or refresh token has expired."""

    def __init__(self) -> None:
        super().__init__("Token has expired")


class InvalidTokenError(AuthenticationError):
    """Token is malformed or signature is invalid."""

    def __init__(self) -> None:
        super().__init__("Invalid token")


class EmailNotVerifiedError(AuthenticationError):
    """Action requires verified email."""

    def __init__(self) -> None:
        super().__init__("Email not verified")


class EmailAlreadyExistsError(AppError):
    """Email is already registered (HTTP 409)."""

    status_code: int = 409

    def __init__(self, email: str | None = None) -> None:
        detail = f"Email already registered: {email}" if email else "Email already registered"
        super().__init__(detail)
