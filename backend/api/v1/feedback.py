"""Feedback API endpoints.

FEATURE FLAG: Controlled by settings.feedback_collection_enabled
TO REMOVE: Delete this file and remove router registration from __init__.py
"""

import logging
from json import dumps
from typing import Annotated

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.auth import security
from backend.core.config import settings
from backend.db.session import get_session
from backend.repositories.feedback import FeedbackRepository
from backend.schemas import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/feedback", tags=["feedback"])


def _validate_feedback_score(metric_type: str, score: int) -> None:
    """Validate score based on metric type."""
    if metric_type == "csat" and not (1 <= score <= 5):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="CSAT score must be between 1 and 5",
        )

    if metric_type == "nps" and not (0 <= score <= 10):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="NPS score must be between 0 and 10",
        )


def _decode_token_payload(token: str) -> dict:
    """Decode JWT token and return full payload including email."""
    try:
        return pyjwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
    except Exception as e:
        logger.warning("Failed to decode token for feedback: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackCreate,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ] = None,
    session: AsyncSession = Depends(get_session),
):
    """Submit user feedback.

    Requires authentication. Feature can be disabled via config.
    """
    if not settings.feedback_collection_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback collection is currently disabled",
        )

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    payload = _decode_token_payload(credentials.credentials)
    user_email = payload.get("email", payload.get("sub", "unknown"))

    _validate_feedback_score(request.metric_type, request.score)

    repo = FeedbackRepository(session)
    feedback = await repo.create(
        user_email=user_email,
        metric_type=request.metric_type,
        score=request.score,
        feedback_text=request.feedback_text,
        context_step=request.context_step,
        ui_variant=request.ui_variant,
        user_segment=request.user_segment,
    )

    logger.info(
        "ANALYTICS_EVENT %s",
        dumps(
            {
                "event_name": "feedback_submitted",
                "metric_type": request.metric_type,
                "score": request.score,
                "context_step": request.context_step,
                "ui_variant": request.ui_variant,
                "user_segment": request.user_segment,
                "user_email": user_email,
                "feedback_id": feedback.id,
            },
            ensure_ascii=False,
        ),
    )

    return feedback
