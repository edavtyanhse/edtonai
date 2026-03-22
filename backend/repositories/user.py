"""User repository."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.user import User


class UserRepository:
    """Data access for User model."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        return await self._session.get(User, user_id)

    async def get_by_email(self, email: str) -> User | None:
        result = await self._session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def create_oauth_user(self, email: str) -> User:
        """Create a user via OAuth (no password, email pre-verified)."""
        user = User(email=email.lower(), password_hash=None, is_email_verified=True)
        self._session.add(user)
        await self._session.flush()
        return user

    async def create(self, email: str, password_hash: str) -> User:
        user = User(email=email.lower(), password_hash=password_hash)
        self._session.add(user)
        await self._session.flush()
        return user

    async def mark_email_verified(self, user_id: UUID) -> None:
        user = await self.get_by_id(user_id)
        if user:
            user.is_email_verified = True
            await self._session.flush()
