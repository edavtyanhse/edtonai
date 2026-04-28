"""Feedback API endpoints.

FEATURE FLAG: Controlled by settings.feedback_collection_enabled
TO REMOVE: Delete this file and remove router registration from __init__.py
"""

from typing import Annotated

from fastapi import APIRouter, Depends, status

from backend.api.dependencies import get_feedback_service
from backend.core.auth import require_auth_payload
from backend.schemas import FeedbackCreate, FeedbackResponse
from backend.services.feedback import FeedbackService

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackCreate,
    payload: Annotated[dict, Depends(require_auth_payload)],
    service: Annotated[FeedbackService, Depends(get_feedback_service)],
):
    """Submit user feedback.

    Requires authentication. Feature can be disabled via config.
    """
    user_email = payload.get("email", payload.get("sub", "unknown"))
    return await service.submit_feedback(
        user_email=user_email,
        metric_type=request.metric_type,
        score=request.score,
        feedback_text=request.feedback_text,
        context_step=request.context_step,
        ui_variant=request.ui_variant,
        user_segment=request.user_segment,
    )
