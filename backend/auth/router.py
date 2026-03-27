"""Auth API endpoints."""

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, Query, Response

from backend.auth.service import AuthService
from backend.containers import Container
from backend.core.auth import require_auth
from backend.schemas.requests.auth import (
    LoginRequest,
    RegisterRequest,
    VerifyEmailRequest,
)
from backend.schemas.responses.auth import AuthResponse, MessageResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"
_REFRESH_MAX_AGE = 30 * 24 * 60 * 60  # 30 days in seconds


def _set_refresh_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        path="/auth",
        max_age=_REFRESH_MAX_AGE,
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(key=_REFRESH_COOKIE, path="/auth")


@router.post("/register", response_model=AuthResponse)
@inject
async def register(
    request: RegisterRequest,
    response: Response,
    service: AuthService = Depends(Provide[Container.auth_service]),
) -> AuthResponse:
    """Register a new user."""
    result = await service.register(request.email, request.password)
    _set_refresh_cookie(response, result.token_pair.refresh_token)
    return AuthResponse(
        access_token=result.token_pair.access_token,
        expires_in=result.token_pair.expires_in,
        user=UserResponse(
            id=str(result.user.id),
            email=result.user.email,
            is_email_verified=result.user.is_email_verified,
        ),
    )


@router.post("/login", response_model=AuthResponse)
@inject
async def login(
    request: LoginRequest,
    response: Response,
    service: AuthService = Depends(Provide[Container.auth_service]),
) -> AuthResponse:
    """Login with email and password."""
    token_pair, user_info = await service.login(request.email, request.password)
    _set_refresh_cookie(response, token_pair.refresh_token)
    return AuthResponse(
        access_token=token_pair.access_token,
        expires_in=token_pair.expires_in,
        user=UserResponse(
            id=str(user_info.id),
            email=user_info.email,
            is_email_verified=user_info.is_email_verified,
        ),
    )


@router.post("/refresh", response_model=AuthResponse)
@inject
async def refresh(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    service: AuthService = Depends(Provide[Container.auth_service]),
) -> AuthResponse:
    """Refresh access token using refresh token cookie."""
    if not refresh_token:
        from backend.errors.auth import InvalidTokenError

        raise InvalidTokenError()

    token_pair, user_info = await service.refresh(UUID(refresh_token))
    _set_refresh_cookie(response, token_pair.refresh_token)
    return AuthResponse(
        access_token=token_pair.access_token,
        expires_in=token_pair.expires_in,
        user=UserResponse(
            id=str(user_info.id),
            email=user_info.email,
            is_email_verified=user_info.is_email_verified,
        ),
    )


@router.post("/logout", response_model=MessageResponse)
@inject
async def logout(
    response: Response,
    refresh_token: str | None = Cookie(default=None, alias=_REFRESH_COOKIE),
    service: AuthService = Depends(Provide[Container.auth_service]),
) -> MessageResponse:
    """Logout — revoke refresh token and clear cookie."""
    if refresh_token:
        try:
            await service.logout(UUID(refresh_token))
        except Exception:
            pass  # Token already invalid — that's fine
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out")


@router.post("/set-cookie", response_model=MessageResponse)
async def set_refresh_cookie(
    response: Response,
    refresh_token: str = Query(...),
) -> MessageResponse:
    """Store refresh token as httpOnly cookie.

    Called by frontend after OAuth callback to persist the refresh token
    on the correct domain (frontend proxy → backend).
    """
    _set_refresh_cookie(response, refresh_token)
    return MessageResponse(message="Cookie set")


@router.post("/verify-email", response_model=MessageResponse)
@inject
async def verify_email(
    request: VerifyEmailRequest,
    service: AuthService = Depends(Provide[Container.auth_service]),
) -> MessageResponse:
    """Verify email using token from link."""
    await service.verify_email(request.token)
    return MessageResponse(message="Email verified successfully")


@router.get("/me", response_model=UserResponse)
@inject
async def get_me(
    user_id: str = Depends(require_auth),
    service: AuthService = Depends(Provide[Container.auth_service]),
) -> UserResponse:
    """Get current user info (requires Bearer token)."""
    user_info = await service.get_current_user(UUID(user_id))
    return UserResponse(
        id=str(user_info.id),
        email=user_info.email,
        is_email_verified=user_info.is_email_verified,
    )
