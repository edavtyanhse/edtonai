"""JWT authentication — custom HS256 tokens.

Drop-in replacement for the old Supabase-based auth.
Same public interface: ``get_current_user_id`` / ``require_auth``.
"""

import logging
from typing import Annotated

import jwt as pyjwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.core.config import settings

logger = logging.getLogger(__name__)

security = HTTPBearer(auto_error=False)


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> str | None:
    """Extract user_id from JWT access token.

    Returns None if no token is provided (allows anonymous access).
    Raises 401 if token is present but invalid/expired.
    """
    if not credentials:
        return None

    payload = _decode_token(credentials.credentials)
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user ID",
        )
    return user_id


def get_current_user_payload(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)],
) -> dict | None:
    """Return decoded JWT payload or None if no token was provided."""
    if not credentials:
        return None
    return _decode_token(credentials.credentials)


def require_auth_payload(
    payload: Annotated[dict | None, Depends(get_current_user_payload)],
) -> dict:
    """Require authentication and return the decoded JWT payload."""
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return payload


def _decode_token(token: str) -> dict:
    """Decode and validate an access token."""
    try:
        return pyjwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except pyjwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def require_auth(
    user_id: Annotated[str | None, Depends(get_current_user_id)],
) -> str:
    """Require authentication — raises 401 if not authenticated."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id
