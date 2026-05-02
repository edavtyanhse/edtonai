"""OAuth 2.0 API endpoints — redirect and callback."""

import hashlib
import hmac
import logging
import secrets
import time
from urllib.parse import urlencode

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, Query
from fastapi.responses import RedirectResponse

from backend.auth.cookies import set_refresh_cookie
from backend.auth.oauth_service import OAuthService
from backend.containers import Container
from backend.core.config import Settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

_STATE_TTL = 300  # 5 minutes


def _sign_state(nonce: str, timestamp: int, secret: str) -> str:
    """Create HMAC-signed state: nonce.timestamp.signature."""
    msg = f"{nonce}.{timestamp}"
    sig = hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()[:16]
    return f"{nonce}.{timestamp}.{sig}"


def _verify_state(state: str, secret: str) -> bool:
    """Verify HMAC-signed state and check TTL."""
    parts = state.split(".")
    if len(parts) != 3:
        return False
    nonce, ts_str, sig = parts
    try:
        timestamp = int(ts_str)
    except ValueError:
        return False
    if time.time() - timestamp > _STATE_TTL:
        return False
    expected = hmac.new(
        secret.encode(), f"{nonce}.{timestamp}".encode(), hashlib.sha256
    ).hexdigest()[:16]
    return hmac.compare_digest(sig, expected)


@router.get("/{provider}")
@inject
async def oauth_redirect(
    provider: str,
    oauth_service: OAuthService = Depends(Provide[Container.oauth_service]),
    settings: Settings = Depends(Provide[Container.config]),
) -> RedirectResponse:
    """Initiate OAuth flow — redirect user to provider's authorize page."""
    nonce = secrets.token_urlsafe(16)
    state = _sign_state(nonce, int(time.time()), settings.jwt_secret_key)

    authorize_url = oauth_service.get_authorize_url(provider, state)
    return RedirectResponse(url=authorize_url, status_code=302)


@router.get("/{provider}/callback")
@inject
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    oauth_service: OAuthService = Depends(Provide[Container.oauth_service]),
    settings: Settings = Depends(Provide[Container.config]),
) -> RedirectResponse:
    """Handle OAuth provider callback — exchange code, issue tokens, redirect to frontend."""
    # Verify signed state (CSRF protection without cookies)
    if not _verify_state(state, settings.jwt_secret_key):
        error_params = urlencode({"error": "Invalid OAuth state. Please try again."})
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?{error_params}",
            status_code=302,
        )

    try:
        token_pair, _user_info = await oauth_service.handle_callback(provider, code)
    except Exception:
        logger.exception("OAuth callback failed for provider=%s", provider)
        error_params = urlencode({"error": "Authentication failed. Please try again."})
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?{error_params}",
            status_code=302,
        )

    response = RedirectResponse(
        url=f"{settings.frontend_url}/oauth/callback",
        status_code=302,
    )
    set_refresh_cookie(
        response,
        token_pair.refresh_token,
        path=settings.refresh_cookie_path,
    )
    return response
