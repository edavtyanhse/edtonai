"""OAuth account repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.oauth_account import OAuthAccount


class OAuthAccountRepository:
    """Data access for OAuthAccount model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_provider_uid(
        self, provider: str, provider_user_id: str
    ) -> OAuthAccount | None:
        """Find existing OAuth link by provider + external user ID."""
        result = await self._session.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id,
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        user_id: UUID,
        provider: str,
        provider_user_id: str,
        email: str | None = None,
        name: str | None = None,
        avatar_url: str | None = None,
    ) -> OAuthAccount:
        """Create a new OAuth account link."""
        account = OAuthAccount(
            user_id=user_id,
            provider=provider,
            provider_user_id=provider_user_id,
            email=email,
            name=name,
            avatar_url=avatar_url,
        )
        self._session.add(account)
        await self._session.flush()
        return account
