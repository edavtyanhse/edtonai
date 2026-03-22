"""Shared token pair creation (used by AuthService and OAuthService)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from backend.auth.jwt import create_access_token
from backend.core.config import Settings
from backend.domain.auth import TokenPair
from backend.repositories.refresh_token_repo import RefreshTokenRepository


async def create_token_pair(
    user_id: UUID,
    email: str,
    refresh_repo: RefreshTokenRepository,
    settings: Settings,
) -> TokenPair:
    """Create access + refresh token pair."""
    access_token = create_access_token(
        user_id=user_id,
        email=email,
        secret=settings.jwt_secret_key,
        expires_minutes=settings.jwt_access_token_expire_minutes,
    )
    expires_at = datetime.now(timezone.utc) + timedelta(
        days=settings.jwt_refresh_token_expire_days
    )
    refresh = await refresh_repo.create(
        user_id=user_id,
        expires_at=expires_at,
    )
    return TokenPair(
        access_token=access_token,
        refresh_token=str(refresh.id),
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )
