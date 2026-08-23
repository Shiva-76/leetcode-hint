"""
memory_store.py — Pure-Python async in-memory store.

Implements the exact Redis API subset used by this app:
  ping() / get() / setex() / incr() / expire()

Used as an automatic fallback when Redis is unavailable.
Replace with real Redis by running:  docker compose up -d
"""
from __future__ import annotations
import asyncio
import time
from typing import Any


class MemoryStore:
    """
    Async in-memory key-value store with TTL support.
    Thread-safe via asyncio (single-threaded event loop).
    """

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}
        self._expiry: dict[str, float] = {}  # key → expiry timestamp

    # ── Redis-compatible API ──────────────────────────────────────────────────

    async def ping(self) -> bool:
        return True

    async def get(self, key: str) -> str | None:
        if self._is_expired(key):
            self._delete(key)
            return None
        return self._data.get(key)

    async def setex(self, key: str, seconds: int, value: str) -> None:
        self._data[key] = value
        self._expiry[key] = time.monotonic() + seconds

    async def incr(self, key: str) -> int:
        if self._is_expired(key):
            self._delete(key)
        current = int(self._data.get(key, 0))
        new_val = current + 1
        self._data[key] = str(new_val)
        return new_val

    async def expire(self, key: str, seconds: int) -> None:
        if key in self._data:
            self._expiry[key] = time.monotonic() + seconds

    async def aclose(self) -> None:
        self._data.clear()
        self._expiry.clear()

    # ── Internals ─────────────────────────────────────────────────────────────

    def _is_expired(self, key: str) -> bool:
        exp = self._expiry.get(key)
        return exp is not None and time.monotonic() > exp

    def _delete(self, key: str) -> None:
        self._data.pop(key, None)
        self._expiry.pop(key, None)
