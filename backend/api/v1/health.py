"""Health-check and configuration endpoints."""

import logging

from fastapi import APIRouter
from sqlalchemy import text

from backend.core.config import MAX_RESUME_CHARS, MAX_VACANCY_CHARS
from backend.db import AsyncSessionLocal

router = APIRouter(tags=["health"])
logger = logging.getLogger(__name__)


@router.get("/health")
async def health_check():
    """Health check endpoint with database connectivity check."""
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as session:
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
async def health_check_v1():
    """V1 Health check — delegates to root health."""
    return await health_check()


@router.get("/v1/limits", tags=["config"])
async def get_limits():
    """Get text input limits for frontend validation."""
    return {
        "max_resume_chars": MAX_RESUME_CHARS,
        "max_vacancy_chars": MAX_VACANCY_CHARS,
    }
