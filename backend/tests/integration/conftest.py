"""Shared fixtures for integration tests (HTTP client, DB, etc.)."""

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from backend.main import app, container


@pytest.fixture
def mock_ai_provider():
    """Mock AI provider for tests that don't need real AI calls."""
    provider = AsyncMock()
    provider.provider_name = "mock-provider"
    provider.model = "mock-model"
    return provider


@pytest.fixture
async def client(mock_ai_provider):
    """Async HTTP client for testing FastAPI endpoints.

    Resets container Singleton providers (engine, session_factory) so
    each test gets connections bound to the **current** event loop.
    """
    # Reset stale Singletons so asyncpg pool is recreated in this loop
    container.async_engine.reset()
    container.session_factory.reset()

    # Also recreate the legacy engine used by get_db / get_session
    from sqlalchemy.ext.asyncio import (
        AsyncSession,
        async_sessionmaker,
        create_async_engine,
    )

    import backend.db.session as _db_session

    _db_session.async_engine = create_async_engine(
        str(container.config().database_url),
        echo=False,
        future=True,
        connect_args={"statement_cache_size": 0},
    )
    _db_session.AsyncSessionLocal = async_sessionmaker(
        bind=_db_session.async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )

    with (
        container.ai_provider_parsing.override(mock_ai_provider),
        container.ai_provider_reasoning.override(mock_ai_provider),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    # Cleanup
    engine = container.async_engine()
    await engine.dispose()
    container.async_engine.reset()
    container.session_factory.reset()

    await _db_session.async_engine.dispose()
