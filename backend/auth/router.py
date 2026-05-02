"""Auth API endpoints."""

from uuid import UUID

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Cookie, Depends, Response

from backend.auth.cookies import clear_refresh_cookie, set_refresh_cookie
from backend.auth.service import AuthService
from backend.containers import Container
from backend.core.auth import require_auth
from backend.core.config import Settings
from backend.schemas.requests.auth import (
    LoginRequest,
    RegisterRequest,
    VerifyEmailRequest,
)
from backend.schemas.responses.auth import AuthResponse, MessageResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

_REFRESH_COOKIE = "refresh_token"


@router.post("/register", response_model=AuthResponse)
@inject
async def register(
    request: RegisterRequest,
    response: Response,
    service: AuthService = Depends(Provide[Container.auth_service]),
    settings: Settings = Depends(Provide[Container.config]),
) -> AuthResponse:
    """Register a new user."""
    result = await service.register(request.email, request.password)
    set_refresh_cookie(
        response,
        result.token_pair.refresh_token,
        path=settings.refresh_cookie_path,
    )
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
    settings: Settings = Depends(Provide[Container.config]),
) -> AuthResponse:
    """Login with email and password."""
    token_pair, user_info = await service.login(request.email, request.password)
    set_refresh_cookie(response, token_pair.refresh_token, path=settings.refresh_cookie_path)
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
    settings: Settings = Depends(Provide[Container.config]),
) -> AuthResponse:
    """Refresh access token using refresh token cookie."""
    if not refresh_token:
        from backend.errors.auth import InvalidTokenError

        raise InvalidTokenError()

    try:
        refresh_token_id = UUID(refresh_token)
    except ValueError:
        from backend.errors.auth import InvalidTokenError

        raise InvalidTokenError()

    token_pair, user_info = await service.refresh(refresh_token_id)
    set_refresh_cookie(response, token_pair.refresh_token, path=settings.refresh_cookie_path)
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
    settings: Settings = Depends(Provide[Container.config]),
) -> MessageResponse:
    """Logout — revoke refresh token and clear cookie."""
    if refresh_token:
        try:
            await service.logout(UUID(refresh_token))
        except Exception:
            pass  # Token already invalid — that's fine
    clear_refresh_cookie(response, path=settings.refresh_cookie_path)
    if settings.refresh_cookie_path != "/auth":
        clear_refresh_cookie(response, path="/auth")
    return MessageResponse(message="Logged out")


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
