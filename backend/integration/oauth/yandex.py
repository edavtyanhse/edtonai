"""Yandex OAuth 2.0 provider."""

from urllib.parse import urlencode

import httpx

from backend.domain.oauth import OAuthUserInfo
from backend.integration.oauth.base import OAuthProvider
from backend.integration.oauth.errors import OAuthEmailNotProvidedError, OAuthProviderError

_AUTHORIZE_URL = "https://oauth.yandex.ru/authorize"
_TOKEN_URL = "https://oauth.yandex.ru/token"
_USERINFO_URL = "https://login.yandex.ru/info"


class YandexOAuthProvider(OAuthProvider):
    """Yandex OAuth 2.0 implementation."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._redirect_uri = redirect_uri

    def get_authorize_url(self, state: str) -> str:
        params = {
            "client_id": self._client_id,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "state": state,
            "force_confirm": "yes",
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
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            if token_resp.status_code != 200:
                raise OAuthProviderError(f"Yandex token exchange failed: {token_resp.text}")

            access_token = token_resp.json().get("access_token")
            if not access_token:
                raise OAuthProviderError("Yandex did not return access_token")

            # Fetch user info
            info_resp = await client.get(
                _USERINFO_URL,
                params={"format": "json"},
                headers={"Authorization": f"OAuth {access_token}"},
            )
            if info_resp.status_code != 200:
                raise OAuthProviderError(f"Yandex userinfo failed: {info_resp.text}")

            data = info_resp.json()
            email = data.get("default_email")
            if not email:
                raise OAuthEmailNotProvidedError("Yandex")

            avatar_id = data.get("default_avatar_id")
            avatar_url = f"https://avatars.yandex.net/get-yapic/{avatar_id}/islands-200" if avatar_id else None

            return OAuthUserInfo(
                provider="yandex",
                provider_user_id=str(data["id"]),
                email=email,
                name=data.get("real_name") or data.get("display_name"),
                avatar_url=avatar_url,
            )
