"""JWT authentication for Supabase tokens."""

import logging
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from backend.core.config import settings

logger = logging.getLogger(__name__)

# Bearer token security scheme
security = HTTPBearer(auto_error=False)

# JWKS client for fetching Supabase public keys
# Cache the client to avoid re-fetching on every request
@lru_cache(maxsize=1)
def get_jwks_client() -> PyJWKClient | None:
    """Get cached JWKS client for Supabase.

    Returns ``None`` when ``supabase_url`` is not configured, in which case
    authentication falls back to legacy HS256 verification only.
    """
    supabase_url = settings.supabase_url
    if not supabase_url:
        logger.warning(
            "SUPABASE_URL is not set — JWKS verification disabled, "
            "falling back to HS256 only",
        )
        return None

    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    logger.info("Initializing JWKS client with URL: %s", jwks_url)
    return PyJWKClient(jwks_url, cache_keys=True, lifespan=3600)


def get_current_user_id(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(security)]
) -> str | None:
    """Extract user_id from Supabase JWT token.

    Returns None if no valid token is provided (allows anonymous access).
    Raises 401 if token is invalid.
    """
    if not credentials:
        return None

    token = credentials.credentials

    try:
        # Try JWKS verification first (for new ECC-signed tokens)
        jwks_client = get_jwks_client()
        if jwks_client is not None:
            try:
                signing_key = jwks_client.get_signing_key_from_jwt(token)
                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=["ES256", "RS256", "HS256"],
                    audience="authenticated",
                )
            except Exception as jwks_error:
                logger.debug("JWKS verification failed, trying legacy HS256: %s", jwks_error)
                jwks_client = None  # fall through to HS256

        if jwks_client is None:
            # Fallback to legacy HS256 with shared secret
            import base64
            key = settings.supabase_jwt_secret
            try:
                payload = jwt.decode(
                    token,
                    key,
                    algorithms=["HS256"],
                    audience="authenticated",
                )
            except jwt.InvalidSignatureError:
                # Try Base64-decoded key
                try:
                    decoded_key = base64.b64decode(key)
                    payload = jwt.decode(
                        token,
                        decoded_key,
                        algorithms=["HS256"],
                        audience="authenticated",
                    )
                except Exception:
                    raise jwt.InvalidSignatureError("Signature verification failed")

        # Extract user ID from 'sub' claim
        user_id = payload.get("sub")
        if not user_id:
            logger.warning("JWT token missing 'sub' claim")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
            )

        return user_id

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning("Invalid JWT token: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


def require_auth(
    user_id: Annotated[str | None, Depends(get_current_user_id)]
) -> str:
    """Require authentication - raises 401 if not authenticated."""
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return user_id
