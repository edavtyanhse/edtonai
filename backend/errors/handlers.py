"""Global FastAPI exception handlers.

Register these in main.py via `register_exception_handlers(app)`.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from backend.errors.base import AppError
from backend.integration.ai.errors import AIError, AIResponseFormatError

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register all global exception handlers on the FastAPI app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        """Handle typed application errors → proper HTTP status + JSON body."""
        logger.warning(
            "AppError | status=%d path=%s detail=%s",
            exc.status_code,
            request.url.path,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @app.exception_handler(AIError)
    async def ai_error_handler(request: Request, exc: AIError) -> JSONResponse:
        """Handle AI integration errors → HTTP 502."""
        logger.error(
            "AIError | path=%s error=%s",
            request.url.path,
            str(exc),
        )
        return JSONResponse(
            status_code=502,
            content={"detail": f"AI provider error: {exc}"},
        )

    @app.exception_handler(AIResponseFormatError)
    async def ai_format_error_handler(request: Request, exc: AIResponseFormatError) -> JSONResponse:
        """Handle malformed AI JSON responses → HTTP 502."""
        logger.error("AIResponseFormatError | path=%s error=%s", request.url.path, str(exc))
        return JSONResponse(
            status_code=502,
            content={"detail": f"AI provider returned invalid response: {exc}"},
        )

    @app.exception_handler(ValueError)
    async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
        """Handle untyped ValueError from services → HTTP 400.

        This is a safety net for ValueError not yet migrated to typed errors.
        """
        logger.warning(
            "ValueError | path=%s detail=%s",
            request.url.path,
            str(exc),
        )
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for unhandled exceptions → HTTP 500 with logging.

        Prevents raw tracebacks from leaking to clients.
        """
        logger.exception(
            "Unhandled exception | path=%s type=%s",
            request.url.path,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
