"""
limiter.py — Sliding-window rate limiter using INCR + EXPIRE.

Works transparently with real Redis or MemoryStore fallback.

Redis schema:
  KEY:   coach:rate:{connection_id}
  VALUE: request count (integer string)
  TTL:   RATE_LIMIT_WINDOW_SECONDS
"""
from __future__ import annotations

from app.cache.redis_client import get_redis
from app.config import settings

RATE_PREFIX = "coach:rate:"


async def check_rate_limit(connection_id: str) -> tuple[bool, int]:
    """
    Atomically increment the request counter for this connection.

    Returns:
        (allowed: bool, current_count: int)
    """
    store = get_redis()
    key = f"{RATE_PREFIX}{connection_id}"

    count = await store.incr(key)
    # Set TTL only on the very first request in the window
    if count == 1:
        await store.expire(key, settings.rate_limit_window_seconds)

    allowed = count <= settings.rate_limit_max_requests
    return allowed, count
