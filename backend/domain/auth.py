"""Auth domain value objects."""

from dataclasses import dataclass
from uuid import UUID


@dataclass
class TokenPair:
    """Access + refresh token pair."""

    access_token: str
    refresh_token: str
    expires_in: int  # seconds


@dataclass
class UserInfo:
    """Public user information."""

    id: UUID
    email: str
    is_email_verified: bool


@dataclass
class RegistrationResult:
    """Result of user registration."""

    user: UserInfo
    token_pair: TokenPair
    verification_sent: bool
