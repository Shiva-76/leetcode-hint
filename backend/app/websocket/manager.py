"""
manager.py — WebSocket ConnectionManager.

Tracks all active WebSocket connections and provides helpers for
sending messages to individual connections or broadcasting.
"""
from __future__ import annotations
import uuid
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        # Maps connection_id → WebSocket
        self._active: dict[str, WebSocket] = {}

    def connect(self, websocket: WebSocket) -> str:
        """Register a new connection. Returns a unique connection ID."""
        conn_id = str(uuid.uuid4())
        self._active[conn_id] = websocket
        print(f"[WS] Connected: {conn_id}  (total: {len(self._active)})")
        return conn_id

    def disconnect(self, conn_id: str) -> None:
        """Remove a connection from the registry."""
        self._active.pop(conn_id, None)
        print(f"[WS] Disconnected: {conn_id}  (total: {len(self._active)})")

    async def send_json(self, conn_id: str, data: dict) -> None:
        """Send a JSON message to a specific connection."""
        ws = self._active.get(conn_id)
        if ws:
            await ws.send_json(data)

    async def send_text(self, conn_id: str, text: str) -> None:
        """Send a raw text message to a specific connection."""
        ws = self._active.get(conn_id)
        if ws:
            await ws.send_text(text)

    @property
    def active_count(self) -> int:
        return len(self._active)


# Module-level singleton shared across the app
manager = ConnectionManager()
