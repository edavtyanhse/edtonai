"""Async database session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from backend.core.config import settings

async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    # Supabase Transaction Pooler (port 6543) does not support prepared statements
    # Use statement_cache_size=0 to disable prepared statement caching
    connect_args={"statement_cache_size": 0},
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for FastAPI to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Alias for consistency
get_session = get_db
