"""Health-check and configuration endpoints."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import text

from backend.api.dependencies import get_session_factory
from backend.core.config import settings

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check(session_factory=Depends(get_session_factory)):
    """Health check endpoint with database connectivity check."""
    db_status = "ok"
    try:
        async with session_factory() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        logger.error("Health check database error: %s: %s", type(e).__name__, e)
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    return {
        "status": status,
        "version": "0.1.0",
        "database": db_status,
    }


@router.get("/v1/health")
async def health_check_v1(session_factory=Depends(get_session_factory)):
    """V1 Health check — delegates to root health."""
    return await health_check(session_factory)


@router.get("/v1/limits", tags=["config"])
async def get_limits():
    """Get text input limits for frontend validation."""
    return {
        "max_resume_chars": settings.max_resume_chars,
        "max_vacancy_chars": settings.max_vacancy_chars,
    }
