"""Feedback API endpoints.

FEATURE FLAG: Controlled by settings.feedback_collection_enabled
TO REMOVE: Delete this file and remove router registration from __init__.py
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.config import settings
from backend.core.auth import get_current_user
from backend.db.session import get_session
from backend.schemas.feedback import FeedbackCreate, FeedbackResponse
from backend.repositories.feedback import FeedbackRepository

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
async def submit_feedback(
    request: FeedbackCreate,
    current_user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    """Submit user feedback.
    
    Requires authentication. Feature can be disabled via config.
    """
    # Check if feedback collection is enabled
    if not settings.feedback_collection_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Feedback collection is currently disabled"
        )
    
    user_email = current_user.get("email")
    if not user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User email not found"
        )
    
    repo = FeedbackRepository(session)
    feedback = await repo.create(
        user_email=user_email,
        feedback_text=request.feedback_text
    )
    
    return feedback
