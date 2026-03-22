"""Abstract OAuth 2.0 provider (Strategy pattern)."""

from abc import ABC, abstractmethod

from backend.domain.oauth import OAuthUserInfo


class OAuthProvider(ABC):
    """Base class for OAuth 2.0 providers.

    Each concrete provider implements authorization URL construction
    and code-to-user-info exchange. The interface is intentionally
    minimal (Interface Segregation Principle).
    """

    @abstractmethod
    def get_authorize_url(self, state: str) -> str:
        """Build the provider's authorization URL for user redirect."""

    @abstractmethod
    async def exchange_code(self, code: str) -> OAuthUserInfo:
        """Exchange authorization code for tokens, then fetch and return user info."""
