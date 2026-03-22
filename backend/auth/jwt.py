"""JWT access token utilities (HS256)."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

import jwt as pyjwt

_ALGORITHM = "HS256"


def create_access_token(
    user_id: UUID,
    email: str,
    secret: str,
    expires_minutes: int = 15,
) -> str:
    """Create a signed HS256 JWT access token."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    return pyjwt.encode(payload, secret, algorithm=_ALGORITHM)


def decode_access_token(token: str, secret: str) -> dict:
    """Decode and validate a JWT access token.

    Returns the full payload dict on success.
    Raises ``pyjwt.ExpiredSignatureError`` or ``pyjwt.InvalidTokenError`` on failure.
    """
    return pyjwt.decode(token, secret, algorithms=[_ALGORITHM])
