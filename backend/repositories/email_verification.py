"""Email verification repository."""

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.email_verification import EmailVerification


class EmailVerificationRepository:
    """Data access for EmailVerification model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        user_id: UUID,
        token: str,
        expires_at: datetime,
    ) -> EmailVerification:
        verification = EmailVerification(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
        )
        self._session.add(verification)
        await self._session.flush()
        return verification

    async def get_valid_token(self, token: str) -> EmailVerification | None:
        result = await self._session.execute(
            select(EmailVerification).where(
                EmailVerification.token == token,
                EmailVerification.is_used.is_(False),
                EmailVerification.expires_at > datetime.now(timezone.utc),
            )
        )
        return result.scalar_one_or_none()

    async def mark_used(self, token: str) -> None:
        verification = await self.get_valid_token(token)
        if verification:
            verification.is_used = True
            await self._session.flush()
