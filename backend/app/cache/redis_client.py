"""
redis_client.py — Async store: real Redis when available, MemoryStore fallback.

Priority:
  1. Try connecting to Redis at REDIS_URL (set in .env)
  2. On failure → fall back to in-process MemoryStore (no external deps)

The fallback is transparent: all callers use get_redis() and get the
same API regardless of which backend is active.
"""
from __future__ import annotations

import redis.asyncio as aioredis

from app.config import settings
from app.cache.memory_store import MemoryStore

# Unified type alias — either real Redis client or our MemoryStore
Store = aioredis.Redis | MemoryStore

_store: Store | None = None
_using_real_redis: bool = False


async def init_redis() -> None:
    """
    Try connecting to real Redis. Fall back to MemoryStore if unavailable.
    Called once in FastAPI lifespan startup.
    """
    global _store, _using_real_redis
    try:
        pool = aioredis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
        )
        await pool.ping()
        _store = pool
        _using_real_redis = True
        print(f"[Store] Redis connected at {settings.redis_url}")
    except Exception as exc:
        _store = MemoryStore()
        _using_real_redis = False
        print(f"[Store] Redis unavailable ({exc.__class__.__name__}) -- using in-memory store.")
        print("[Store] For persistence, run: docker compose up -d")


async def close_redis() -> None:
    """Close the store. Called once in FastAPI lifespan shutdown."""
    global _store, _using_real_redis
    if _store:
        await _store.aclose()
        _store = None
        _using_real_redis = False
        print("[Store] Connection closed.")


def get_redis() -> Store:
    """
    Return the active store (Redis or MemoryStore).
    Always returns a valid object after init_redis() has been called.
    """
    if _store is None:
        raise RuntimeError("Store not initialised. Call init_redis() first.")
    return _store


def is_redis_available() -> bool:
    """Returns True only when connected to a real Redis instance."""
    return _using_real_redis
