"""Feedback API endpoints.

FEATURE FLAG: Controlled by settings.feedback_collection_enabled
TO REMOVE: Delete this file and remove router registration from __init__.py
"""
import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

import jwt

from backend.core.config import settings
from backend.core.auth import security, get_jwks_client
from backend.db.session import get_session
from backend.schemas.feedback import FeedbackCreate, FeedbackResponse
from backend.repositories.feedback import FeedbackRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _decode_token_payload(token: str) -> dict:
    """Decode JWT token and return full payload including email."""
    try:
        try:
            jwks_client = get_jwks_client()
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            return jwt.decode(
                token, signing_key.key,
                algorithms=["ES256", "RS256", "HS256"],
                audience="authenticated",
            )
        except Exception:
            import base64
            key = settings.supabase_jwt_secret
            try:
                return jwt.decode(token, key, algorithms=["HS256"], audience="authenticated")
            except jwt.InvalidSignatureError:
                decoded_key = base64.b64decode(key)
                return jwt.decode(token, decoded_key, algorithms=["HS256"], audience="authenticated")
    except Exception as e:
        logger.warning(f"Failed to decode token for feedback: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackCreate,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)] = None,
    session: AsyncSession = Depends(get_session),
):
    """Submit user feedback.
    
    Requires authentication. Feature can be disabled via config.
    """
    if not settings.feedback_collection_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback collection is currently disabled"
        )
    
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    payload = _decode_token_payload(credentials.credentials)
    user_email = payload.get("email", payload.get("sub", "unknown"))
    
    repo = FeedbackRepository(session)
    feedback = await repo.create(
        user_email=user_email,
        feedback_text=request.feedback_text
    )
    
    return feedback
