"""Deprecated DB session helpers.

Runtime database session management is owned by ``backend.containers.Container``.
This module remains only to fail fast if old router-level DB dependencies are
reintroduced.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

async_engine = None
AsyncSessionLocal = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Deprecated FastAPI dependency.

    Use ``backend.api.dependencies.get_session_factory`` or service providers
    from the DI container instead.
    """
    raise RuntimeError("Use Container.session_factory instead of backend.db.session")
    yield  # pragma: no cover


# Alias for consistency
get_session = get_db
