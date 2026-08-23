"""
router.py — WebSocket endpoint: ws://localhost:8000/ws/coach

Full request pipeline per message:
  1. Parse + validate JSON payload (Pydantic CoachRequest)
  2. Check rate limit  →  send RATE_LIMIT and continue if exceeded
  3. Compute SHA-256 hash of the request semantics
  4. Redis cache lookup  →  if HIT: stream cached text + DONE
  5. Cache MISS: call stub/LLM streamer, collect full text
  6. Cache the full response in Redis
  7. Send DONE

Token streaming protocol:
  { "type": "TOKEN",      "token": "..." }   ← one per word/chunk
  { "type": "CACHE_HIT",  "cached": true  }  ← only on cache hits
  { "type": "DONE"                         }  ← always the last message
  { "type": "ERROR",      "message": "..." }  ← validation / internal errors
  { "type": "RATE_LIMIT", "message": "..." }  ← rate limit breach
"""
from __future__ import annotations
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.schemas import CoachRequest
from app.websocket.manager import manager
from app.cache.ast_cache import get_cached_hint, set_cached_hint
from app.rate_limit.limiter import check_rate_limit
from app.utils.hashing import compute_request_hash
from app.llm.stub_streamer import stream_stub_response

router = APIRouter()


@router.websocket("/ws/coach")
async def coach_websocket(websocket: WebSocket):
    await websocket.accept()
    conn_id = manager.connect(websocket)

    try:
        while True:
            # ── 1. Receive raw message ────────────────────────────────────────
            raw = await websocket.receive_text()

            try:
                payload = json.loads(raw)
                req = CoachRequest(**payload)
            except (json.JSONDecodeError, ValidationError) as exc:
                await websocket.send_json({
                    "type": "ERROR",
                    "message": f"Invalid payload: {exc}"
                })
                continue

            # ── 2. Rate limit ─────────────────────────────────────────────────
            allowed, count = await check_rate_limit(conn_id)
            if not allowed:
                await websocket.send_json({
                    "type": "RATE_LIMIT",
                    "message": f"Rate limit exceeded ({count} requests). "
                               "Please wait before sending another request.",
                    "retry_after": 60,
                })
                continue

            # ── 3. Compute semantic hash ──────────────────────────────────────
            req_hash = compute_request_hash(req)

            # ── 4. Cache lookup ───────────────────────────────────────────────
            cached_text = await get_cached_hint(req_hash)

            if cached_text:
                # ── Cache HIT: stream cached text word-by-word ──────────────
                await websocket.send_json({"type": "CACHE_HIT", "cached": True})
                words = cached_text.split(" ")
                for i, word in enumerate(words):
                    token = word if i == len(words) - 1 else word + " "
                    await websocket.send_json({"type": "TOKEN", "token": token})
                    await asyncio.sleep(0.015)  # natural feel even from cache
                await websocket.send_json({"type": "DONE"})
                continue

            # ── 5. Cache MISS: stream from LLM/stub ──────────────────────────
            full_text_parts: list[str] = []

            async for token in stream_stub_response(req):
                await websocket.send_json({"type": "TOKEN", "token": token})
                full_text_parts.append(token)

            # ── 6. Cache the full response ────────────────────────────────────
            full_text = "".join(full_text_parts)
            if full_text.strip():
                await set_cached_hint(req_hash, full_text)

            # ── 7. Signal completion ──────────────────────────────────────────
            await websocket.send_json({"type": "DONE"})

    except WebSocketDisconnect:
        manager.disconnect(conn_id)
    except Exception as exc:
        print(f"[WS] Unhandled error on {conn_id}: {exc}")
        try:
            await websocket.send_json({"type": "ERROR", "message": "Internal server error."})
        except Exception:
            pass
        manager.disconnect(conn_id)
