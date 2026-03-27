"""VK OAuth 2.0 provider."""

from urllib.parse import urlencode

import httpx

from backend.domain.oauth import OAuthUserInfo
from backend.integration.oauth.base import OAuthProvider
from backend.integration.oauth.errors import (
    OAuthEmailNotProvidedError,
    OAuthProviderError,
)

_AUTHORIZE_URL = "https://oauth.vk.com/authorize"
_TOKEN_URL = "https://oauth.vk.com/access_token"
_API_URL = "https://api.vk.com/method/users.get"
_API_VERSION = "5.199"


class VkOAuthProvider(OAuthProvider):
    """VK OAuth 2.0 implementation."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "scope": "email",
            "state": state,
            "display": "page",
            "v": _API_VERSION,
        }
        return f"{_AUTHORIZE_URL}?{urlencode(params)}"

    async def exchange_code(self, code: str) -> OAuthUserInfo:
        async with httpx.AsyncClient(timeout=15.0) as client:
            # Exchange code for tokens (VK returns email in token response)
            token_resp = await client.get(
                _TOKEN_URL,
                params={
                    "code": code,
                    "client_id": self._client_id,
                    "client_secret": self._client_secret,
                    "redirect_uri": self._redirect_uri,
                },
            )
            if token_resp.status_code != 200:
                raise OAuthProviderError(f"VK token exchange failed: {token_resp.text}")

            token_data = token_resp.json()
            access_token = token_data.get("access_token")
            if not access_token:
                raise OAuthProviderError("VK did not return access_token")

            user_id = str(token_data.get("user_id", ""))
            email = token_data.get("email")
            if not email:
                raise OAuthEmailNotProvidedError("VK")

            # Fetch user profile for name and avatar
            info_resp = await client.get(
                _API_URL,
                params={
                    "access_token": access_token,
                    "user_ids": user_id,
                    "fields": "photo_200,first_name,last_name",
                    "v": _API_VERSION,
                },
            )
            name = None
            avatar_url = None
            if info_resp.status_code == 200:
                users = info_resp.json().get("response", [])
                if users:
                    user = users[0]
                    first = user.get("first_name", "")
                    last = user.get("last_name", "")
                    name = f"{first} {last}".strip() or None
                    avatar_url = user.get("photo_200")

            return OAuthUserInfo(
                provider="vk",
                provider_user_id=user_id,
                email=email,
                name=name,
                avatar_url=avatar_url,
            )
