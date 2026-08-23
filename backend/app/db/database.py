"""
database.py - Async SQLAlchemy engine + session factory.

Dev  → SQLite  (sqlite+aiosqlite:///./coach.db)   ← zero setup, auto-fallback
Prod → PostgreSQL (postgresql+asyncpg://...)       ← set DATABASE_URL in .env

The engine is chosen automatically based on DATABASE_URL.
All code above this layer uses AsyncSession and never touches the URL.
"""
from __future__ import annotations

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.config import settings

# ── Engine ────────────────────────────────────────────────────────────────────

def _make_engine():
    url = settings.database_url
    kwargs: dict = {"echo": settings.app_env == "development"}

    # SQLite needs check_same_thread=False (async driver handles safety itself)
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}

    return create_async_engine(url, **kwargs)


engine = _make_engine()

# ── Session factory ───────────────────────────────────────────────────────────

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# ── Declarative base ──────────────────────────────────────────────────────────

class Base(DeclarativeBase):
    pass


# ── Dependency / context manager ──────────────────────────────────────────────

async def get_db() -> AsyncSession:
    """FastAPI dependency — yields an async session, auto-closes on exit."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Create all tables. Called once on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print(f"[DB] Tables ready  ({settings.database_url.split('://')[0]})")


async def close_db() -> None:
    """Dispose engine. Called once on shutdown."""
    await engine.dispose()
    print("[DB] Engine disposed.")
