"""SQLAlchemy async engine and session factory.

Lazy initialization — engine created on first use, not at import time.
This allows tests to import app modules without a live database.
"""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


_engine = None
_AsyncSessionLocal = None


def _get_engine():
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            settings.database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
        )
    return _engine


def _get_session_factory():
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            _get_engine(), class_=AsyncSession, expire_on_commit=False
        )
    return _AsyncSessionLocal


async def get_db() -> AsyncSession:
    """FastAPI dependency injection: get a database session."""
    async with _get_session_factory()() as session:
        try:
            yield session
        finally:
            await session.close()


# Backward-compatible lazy proxy for scripts that use AsyncSessionLocal directly.
class _AsyncSessionLocalProxy:
    def __call__(self):
        return _get_session_factory()()
    def __getattr__(self, name):
        return getattr(_get_session_factory(), name)


AsyncSessionLocal = _AsyncSessionLocalProxy()
