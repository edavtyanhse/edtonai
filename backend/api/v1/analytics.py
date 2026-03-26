"""Analytics API endpoints for behavior event logging."""

import logging
from datetime import UTC, datetime
from json import dumps
from typing import Annotated

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from backend.core.auth import security
from backend.core.config import settings
from backend.schemas import AnalyticsEventAcceptedResponse, AnalyticsEventCreate

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _decode_token_payload(token: str) -> dict:
    """Decode JWT token and return full payload including email."""
    try:
        return pyjwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=["HS256"],
        )
    except Exception as e:
        logger.warning("Failed to decode token for analytics: %s", e)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        )


@router.post(
    "/events",
    response_model=AnalyticsEventAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_analytics_event(
    request: AnalyticsEventCreate,
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(security)
    ] = None,
):
    """Ingest behavior analytics event and write it to application logs."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required"
        )

    payload = _decode_token_payload(credentials.credentials)
    user_email = payload.get("email", payload.get("sub", "unknown"))

    logger.info(
        "ANALYTICS_EVENT %s",
        dumps(
            {
                "event_name": request.event_name,
                "session_id": request.session_id,
                "step": request.step,
                "ui_variant": request.ui_variant,
                "user_segment": request.user_segment,
                "occurred_at": (
                    request.occurred_at.isoformat() if request.occurred_at else None
                ),
                "properties": request.properties,
                "user_email": user_email,
            },
            ensure_ascii=False,
        ),
    )

    return AnalyticsEventAcceptedResponse(
        status="accepted",
        event_name=request.event_name,
        session_id=request.session_id,
        logged_at=datetime.now(UTC),
    )
