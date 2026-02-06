"""FastAPI application entry point."""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy import text

from backend.api import v1_router
from backend.core.config import settings, MAX_RESUME_CHARS, MAX_VACANCY_CHARS
from backend.core.logging import setup_logging, request_id_ctx
from backend.db import async_engine, Base, AsyncSessionLocal


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: create tables on startup."""
    setup_logging()

    # Create tables (for development; use Alembic in production)
    # async with async_engine.begin() as conn:
    #     await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    await async_engine.dispose()


app = FastAPI(
    title="Resume Adapter API",
    description="API for adapting resumes to job vacancies using AI",
    version="0.1.0",
    lifespan=lifespan,
)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    """Add request_id to each request for tracing."""
    req_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    request_id_ctx.set(req_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint with database connectivity check."""
    db_status = "ok"
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
    except Exception as e:
        import logging
        logging.error(f"Health check database error: {type(e).__name__}: {e}")
        db_status = "error"

    status = "ok" if db_status == "ok" else "degraded"
    return {
        "status": status,
        "version": "0.1.0",
        "database": db_status,
    }


@app.get("/v1/health", tags=["health"])
async def health_check_v1():
    """V1 Health check endpoint with database connectivity check."""
    return await health_check()


@app.get("/v1/limits", tags=["config"])
async def get_limits():
    """Get text input limits for frontend validation."""
    return {
        "max_resume_chars": MAX_RESUME_CHARS,
        "max_vacancy_chars": MAX_VACANCY_CHARS,
    }


# Include API routers
app.include_router(v1_router)
