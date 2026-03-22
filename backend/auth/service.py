"""AuthService — registration, login, refresh, email verification."""

import logging
import secrets
from datetime import datetime, timedelta, timezone
from uuid import UUID

from backend.auth.password import hash_password, verify_password
from backend.auth.tokens import create_token_pair
from backend.core.config import Settings
from backend.domain.auth import RegistrationResult, TokenPair, UserInfo
from backend.errors.auth import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    InvalidTokenError,
    TokenExpiredError,
)
from backend.integration.email.service import EmailService
from backend.repositories.email_verification import EmailVerificationRepository
from backend.repositories.refresh_token_repo import RefreshTokenRepository
from backend.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class AuthService:
    """Handles user authentication lifecycle."""

    def __init__(
        self,
        user_repo: UserRepository,
        refresh_token_repo: RefreshTokenRepository,
        email_verification_repo: EmailVerificationRepository,
        email_service: EmailService,
        settings: Settings,
    ) -> None:
        self._user_repo = user_repo
        self._refresh_repo = refresh_token_repo
        self._email_repo = email_verification_repo
        self._email_service = email_service
        self._settings = settings

    # ── Registration ───────────────────────────────────────────────

    async def register(self, email: str, password: str) -> RegistrationResult:
        """Register a new user, send verification email, return tokens."""
        existing = await self._user_repo.get_by_email(email)
        if existing:
            raise EmailAlreadyExistsError(email)

        pw_hash = hash_password(password)
        user = await self._user_repo.create(email, pw_hash)

        token_pair = await self._create_token_pair(user.id, user.email)

        # Send verification email (best-effort, don't fail registration)
        verification_sent = False
        try:
            verification_token = secrets.token_urlsafe(48)
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)
            await self._email_repo.create(user.id, verification_token, expires_at)
            await self._email_service.send_verification_email(
                email=user.email,
                token=verification_token,
                frontend_url=self._settings.frontend_url,
            )
            verification_sent = True
        except Exception:
            logger.exception("Failed to send verification email to %s", email)

        return RegistrationResult(
            user=UserInfo(id=user.id, email=user.email, is_email_verified=False),
            token_pair=token_pair,
            verification_sent=verification_sent,
        )

    # ── Login ──────────────────────────────────────────────────────

    async def login(self, email: str, password: str) -> tuple[TokenPair, UserInfo]:
        """Authenticate user by email/password, return tokens + user info."""
        user = await self._user_repo.get_by_email(email)
        if not user or not user.password_hash:
            raise InvalidCredentialsError()
        if not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()
        if not user.is_active:
            raise InvalidCredentialsError()

        token_pair = await self._create_token_pair(user.id, user.email)
        user_info = UserInfo(
            id=user.id,
            email=user.email,
            is_email_verified=user.is_email_verified,
        )
        return token_pair, user_info

    # ── Refresh ────────────────────────────────────────────────────

    async def refresh(self, refresh_token_id: UUID) -> tuple[TokenPair, UserInfo]:
        """Rotate refresh token and issue new access token."""
        token = await self._refresh_repo.get_valid_token(refresh_token_id)
        if not token:
            raise TokenExpiredError()

        # Revoke old token (rotation)
        await self._refresh_repo.revoke(token.id)

        user = await self._user_repo.get_by_id(token.user_id)
        if not user or not user.is_active:
            raise InvalidTokenError()

        new_pair = await self._create_token_pair(user.id, user.email)
        user_info = UserInfo(
            id=user.id,
            email=user.email,
            is_email_verified=user.is_email_verified,
        )
        return new_pair, user_info

    # ── Logout ─────────────────────────────────────────────────────

    async def logout(self, refresh_token_id: UUID) -> None:
        """Revoke a refresh token."""
        await self._refresh_repo.revoke(refresh_token_id)

    # ── Email verification ─────────────────────────────────────────

    async def verify_email(self, token: str) -> UserInfo:
        """Verify email using verification token."""
        verification = await self._email_repo.get_valid_token(token)
        if not verification:
            raise InvalidTokenError()

        await self._email_repo.mark_used(token)
        await self._user_repo.mark_email_verified(verification.user_id)

        user = await self._user_repo.get_by_id(verification.user_id)
        if not user:
            raise InvalidTokenError()

        return UserInfo(
            id=user.id,
            email=user.email,
            is_email_verified=True,
        )

    # ── Get current user ───────────────────────────────────────────

    async def get_current_user(self, user_id: UUID) -> UserInfo:
        """Get user info by ID."""
        user = await self._user_repo.get_by_id(user_id)
        if not user:
            raise InvalidTokenError()
        return UserInfo(
            id=user.id,
            email=user.email,
            is_email_verified=user.is_email_verified,
        )

    # ── Private helpers ────────────────────────────────────────────

    async def _create_token_pair(self, user_id: UUID, email: str) -> TokenPair:
        """Create access + refresh token pair (delegates to shared helper)."""
        return await create_token_pair(user_id, email, self._refresh_repo, self._settings)
