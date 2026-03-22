"""OAuthService — handles OAuth login/registration flow."""

import logging
from uuid import UUID

from backend.auth.tokens import create_token_pair
from backend.core.config import Settings
from backend.domain.auth import TokenPair, UserInfo
from backend.integration.oauth.base import OAuthProvider
from backend.integration.oauth.errors import UnsupportedOAuthProviderError
from backend.repositories.oauth_account import OAuthAccountRepository
from backend.repositories.refresh_token_repo import RefreshTokenRepository
from backend.repositories.user import UserRepository

logger = logging.getLogger(__name__)


class OAuthService:
    """Orchestrates OAuth login: provider code exchange, user creation/linking, token issuance."""

    def __init__(
        self,
        user_repo: UserRepository,
        oauth_account_repo: OAuthAccountRepository,
        refresh_token_repo: RefreshTokenRepository,
        settings: Settings,
        providers: dict[str, OAuthProvider],
    ) -> None:
        self._user_repo = user_repo
        self._oauth_repo = oauth_account_repo
        self._refresh_repo = refresh_token_repo
        self._settings = settings
        self._providers = providers

    def get_authorize_url(self, provider_name: str, state: str) -> str:
        """Build authorization URL for the given provider."""
        provider = self._get_provider(provider_name)
        return provider.get_authorize_url(state)

    async def handle_callback(
        self, provider_name: str, code: str
    ) -> tuple[TokenPair, UserInfo]:
        """Exchange code, create/link user, issue tokens.

        Logic:
        1. Exchange code → OAuthUserInfo
        2. Check if OAuthAccount exists for (provider, provider_user_id)
           → Yes: load linked user, issue tokens
        3. Check if User exists with same email
           → Yes: link OAuth account to existing user, issue tokens
        4. Create new user + OAuth link, issue tokens
        """
        provider = self._get_provider(provider_name)
        oauth_info = await provider.exchange_code(code)

        # Case A: OAuth account already linked
        existing_account = await self._oauth_repo.get_by_provider_uid(
            oauth_info.provider, oauth_info.provider_user_id
        )
        if existing_account:
            user = await self._user_repo.get_by_id(existing_account.user_id)
            if not user:
                raise UnsupportedOAuthProviderError(provider_name)
            logger.info("OAuth login: existing link for %s user_id=%s", provider_name, user.id)
            return await self._issue_tokens(user.id, user.email)

        # Case B: User with same email exists → link
        existing_user = await self._user_repo.get_by_email(oauth_info.email)
        if existing_user:
            await self._oauth_repo.create(
                user_id=existing_user.id,
                provider=oauth_info.provider,
                provider_user_id=oauth_info.provider_user_id,
                email=oauth_info.email,
                name=oauth_info.name,
                avatar_url=oauth_info.avatar_url,
            )
            # Mark email as verified since OAuth provider confirmed it
            if not existing_user.is_email_verified:
                await self._user_repo.mark_email_verified(existing_user.id)
            logger.info("OAuth login: linked %s to existing user %s", provider_name, existing_user.id)
            return await self._issue_tokens(existing_user.id, existing_user.email)

        # Case C: New user
        new_user = await self._user_repo.create_oauth_user(oauth_info.email)
        await self._oauth_repo.create(
            user_id=new_user.id,
            provider=oauth_info.provider,
            provider_user_id=oauth_info.provider_user_id,
            email=oauth_info.email,
            name=oauth_info.name,
            avatar_url=oauth_info.avatar_url,
        )
        logger.info("OAuth login: created new user %s via %s", new_user.id, provider_name)
        return await self._issue_tokens(new_user.id, new_user.email)

    def _get_provider(self, name: str) -> OAuthProvider:
        provider = self._providers.get(name)
        if not provider:
            raise UnsupportedOAuthProviderError(name)
        return provider

    async def _issue_tokens(self, user_id: UUID, email: str) -> tuple[TokenPair, UserInfo]:
        token_pair = await create_token_pair(user_id, email, self._refresh_repo, self._settings)
        user = await self._user_repo.get_by_id(user_id)
        user_info = UserInfo(
            id=user_id,
            email=email,
            is_email_verified=user.is_email_verified if user else False,
        )
        return token_pair, user_info
