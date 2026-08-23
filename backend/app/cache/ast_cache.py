"""
ast_cache.py — Store and retrieve cached hint text keyed by AST hash.

Redis schema:
  KEY:   coach:cache:{sha256_hash}
  VALUE: full hint text (string)
  TTL:   CACHE_TTL_SECONDS (default 1 hour)
"""
from __future__ import annotations

from app.cache.redis_client import get_redis
from app.config import settings

CACHE_PREFIX = "coach:cache:"


async def get_cached_hint(request_hash: str) -> str | None:
    """
    Look up a cached hint by its request hash.
    Returns the full hint text if found, else None.
    Works with both real Redis and MemoryStore fallback.
    """
    store = get_redis()
    key = f"{CACHE_PREFIX}{request_hash}"
    return await store.get(key)


async def set_cached_hint(request_hash: str, text: str) -> None:
    """
    Store a completed hint text with a TTL.
    Works with both real Redis and MemoryStore fallback.
    """
    store = get_redis()
    key = f"{CACHE_PREFIX}{request_hash}"
    await store.setex(key, settings.cache_ttl_seconds, text)
