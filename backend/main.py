"""FastAPI application entry point."""

import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from backend.api import v1_router
from backend.api.v1.health import router as health_router
from backend.auth.oauth_router import router as oauth_router
from backend.auth.router import router as auth_router
from backend.containers import Container
from backend.core.logging import request_id_ctx, setup_logging
from backend.errors.handlers import register_exception_handlers

# ── DI Container ──────────────────────────────────────────────────

container = Container()
container.wire()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize logging and dispose engine on shutdown."""
    setup_logging()

    engine = container.async_engine()

    # Optional development-only bootstrap.
    # Disabled by default so production startup does not fail if DB is not yet reachable
    # or the configured connection points to a pooled/protected database.
    if container.config().db_auto_create:
        from backend.db import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    yield

    # Cleanup
    await engine.dispose()


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
    # Reset DI session resource per request so each request gets a fresh session.
    # This prevents PendingRollbackError from poisoning subsequent requests.
    container.session.reset()
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response


# CORS — required for httpOnly cookie auth
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        container.config().frontend_url,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global exception handlers
register_exception_handlers(app)

# Include API routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(oauth_router)
app.include_router(v1_router)
