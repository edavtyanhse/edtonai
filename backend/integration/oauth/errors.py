"""OAuth integration errors."""

from backend.errors.base import AppError


class OAuthError(AppError):
    """Base OAuth error (HTTP 400)."""

    status_code: int = 400


class OAuthProviderError(OAuthError):
    """Provider returned an error during code exchange or user info fetch."""


class OAuthEmailNotProvidedError(OAuthError):
    """Provider did not return an email address."""

    def __init__(self, provider: str) -> None:
        super().__init__(f"{provider} did not provide an email address. Email is required for registration.")


class UnsupportedOAuthProviderError(OAuthError):
    """Unknown provider name requested."""

    status_code: int = 404

    def __init__(self, provider: str) -> None:
        super().__init__(f"Unsupported OAuth provider: {provider}")
