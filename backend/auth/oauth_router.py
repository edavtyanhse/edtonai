"""OAuth 2.0 API endpoints — redirect and callback."""

import secrets
from urllib.parse import urlencode

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, Query, Response
from fastapi.responses import RedirectResponse

from backend.auth.oauth_service import OAuthService
from backend.containers import Container
from backend.core.config import Settings

router = APIRouter(prefix="/auth/oauth", tags=["oauth"])

_STATE_COOKIE = "oauth_state"
_STATE_MAX_AGE = 300  # 5 minutes


@router.get("/{provider}")
@inject
async def oauth_redirect(
    provider: str,
    response: Response,
    oauth_service: OAuthService = Depends(Provide[Container.oauth_service]),
) -> RedirectResponse:
    """Initiate OAuth flow — redirect user to provider's authorize page."""
    state = secrets.token_urlsafe(32)

    authorize_url = oauth_service.get_authorize_url(provider, state)

    redirect = RedirectResponse(url=authorize_url, status_code=302)
    redirect.set_cookie(
        key=_STATE_COOKIE,
        value=state,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=_STATE_MAX_AGE,
    )
    return redirect


@router.get("/{provider}/callback")
@inject
async def oauth_callback(
    provider: str,
    code: str = Query(...),
    state: str = Query(...),
    oauth_state: str | None = Cookie(default=None, alias=_STATE_COOKIE),
    oauth_service: OAuthService = Depends(Provide[Container.oauth_service]),
    settings: Settings = Depends(Provide[Container.config]),
) -> RedirectResponse:
    """Handle OAuth provider callback — exchange code, issue tokens, redirect to frontend."""
    # CSRF check
    if not oauth_state or oauth_state != state:
        error_params = urlencode({"error": "Invalid OAuth state. Please try again."})
        return RedirectResponse(
            url=f"{settings.frontend_url}/login?{error_params}",
            status_code=302,
        )

    token_pair, user_info = await oauth_service.handle_callback(provider, code)

    # Redirect to frontend callback page with access token
    params = urlencode({
        "access_token": token_pair.access_token,
        "expires_in": str(token_pair.expires_in),
    })

    redirect = RedirectResponse(
        url=f"{settings.frontend_url}/oauth/callback?{params}",
        status_code=302,
    )

    # Set refresh token cookie
    redirect.set_cookie(
        key="refresh_token",
        value=token_pair.refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth",
        max_age=30 * 24 * 60 * 60,
    )

    # Clear state cookie
    redirect.delete_cookie(key=_STATE_COOKIE)

    return redirect
