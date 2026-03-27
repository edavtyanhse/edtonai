"""Google OAuth 2.0 provider."""

from urllib.parse import urlencode

import httpx

from backend.domain.oauth import OAuthUserInfo
from backend.integration.oauth.base import OAuthProvider
from backend.integration.oauth.errors import (
    OAuthEmailNotProvidedError,
    OAuthProviderError,
)

_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"
_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


class GoogleOAuthProvider(OAuthProvider):
    """Google OAuth 2.0 implementation."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",
            "prompt": "select_account",
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthUserInfo:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Exchange code for tokens
            token_resp = await client.post(
                _TOKEN_URL,
                data={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                raise OAuthProviderError(
                    f"Google token exchange failed: {token_resp.text}"
                )

            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise OAuthProviderError("Google did not return access_token")

            # Fetch user info
            info_resp = await client.get(
                _USERINFO_URL,
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if info_resp.status_code != 200:
                raise OAuthProviderError(f"Google userinfo failed: {info_resp.text}")

            data = info_resp.json()
            email = data.get("email")
            if not email:
                raise OAuthEmailNotProvidedError("Google")

            return OAuthUserInfo(
                provider="google",
                provider_user_id=str(data["id"]),
                email=email,
                name=data.get("name"),
                avatar_url=data.get("picture"),
            )
