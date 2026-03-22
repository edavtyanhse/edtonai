"""OAuth domain value objects."""

from dataclasses import dataclass


@dataclass
class OAuthUserInfo:
    """Normalized user info from any OAuth provider."""

    provider: str
    provider_user_id: str
    email: str
    name: str | None = None
    avatar_url: str | None = None
