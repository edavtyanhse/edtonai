"""Shared auth cookie helpers."""

from fastapi import Response

_REFRESH_COOKIE = "refresh_token"
_REFRESH_MAX_AGE = 30 * 24 * 60 * 60  # 30 days in seconds


def set_refresh_cookie(
    response: Response,
    token: str,
    path: str = "/",
) -> None:
    """Store refresh token in an httpOnly cookie."""
    response.set_cookie(
        key=_REFRESH_COOKIE,
        value=token,
        httponly=True,
        secure=True,
        samesite="lax",
        path=path,
        max_age=_REFRESH_MAX_AGE,
    )


def clear_refresh_cookie(response: Response, path: str = "/") -> None:
    """Clear refresh token cookie."""
    response.delete_cookie(key=_REFRESH_COOKIE, path=path)
