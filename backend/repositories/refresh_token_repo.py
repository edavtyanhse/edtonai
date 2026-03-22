"""Refresh token repository."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    """Data access for RefreshToken model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        expires_at: datetime,
        device_info: str | None = None,
    ) -> RefreshToken:
        token = RefreshToken(
            user_id=user_id,
            expires_at=expires_at,
            device_info=device_info,
        )
        self._session.add(token)
        await self._session.flush()
        return token

    async def get_valid_token(self, token_id: UUID) -> RefreshToken | None:
        result = await self._session.execute(
            select(RefreshToken).where(
                RefreshToken.id == token_id,
                RefreshToken.is_revoked.is_(False),
                RefreshToken.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def revoke(self, token_id: UUID) -> None:
        await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.id == token_id)
            .values(is_revoked=True)
        )

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        result = await self._session.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id, RefreshToken.is_revoked.is_(False))
            .values(is_revoked=True)
        )
        return result.rowcount  # type: ignore[return-value]
