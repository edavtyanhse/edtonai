"""Analytics API endpoints for behavior event logging."""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import get_analytics_service
from backend.core.auth import require_auth_payload
from backend.schemas import AnalyticsEventAcceptedResponse, AnalyticsEventCreate
from backend.services.analytics import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.post(
    "/events",
    response_model=AnalyticsEventAcceptedResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def ingest_analytics_event(
    request: AnalyticsEventCreate,
    payload: Annotated[dict, Depends(require_auth_payload)],
    service: Annotated[AnalyticsService, Depends(get_analytics_service)],
):
    """Ingest behavior analytics event and write it to application logs."""
    user_email = payload.get("email", payload.get("sub", "unknown"))
    accepted = await service.ingest_event(
        user_email=user_email,
        event_name=request.event_name,
        session_id=request.session_id,
        step=request.step,
        ui_variant=request.ui_variant,
        user_segment=request.user_segment,
        occurred_at=request.occurred_at,
        properties=request.properties,
    )
    return AnalyticsEventAcceptedResponse(
        status=accepted.status,
        event_name=accepted.event_name,
        session_id=accepted.session_id,
        logged_at=accepted.logged_at,
    )
