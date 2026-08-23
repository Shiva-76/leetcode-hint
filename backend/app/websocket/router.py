"""
router.py — WebSocket endpoint: ws://localhost:8000/ws/coach

Full pipeline per message:
  1. Parse + validate JSON (Pydantic CoachRequest)
  2. Rate limit check
  3. SHA-256 semantic hash
  4. Redis/Memory cache lookup  →  HIT: stream cached text
  5. Fetch problem context from DB (real complexity targets)
  6. Cache MISS: stream from LLM/stub with problem context
  7. Cache the full response + store in Qdrant
  8. Send DONE

Token streaming protocol:
  { "type": "TOKEN",      "token": "..." }
  { "type": "CACHE_HIT",  "cached": true }
  { "type": "PROBLEM_CTX","title":"...","tier_info":{...} }  ← new in Phase 3
  { "type": "DONE"                       }
  { "type": "ERROR",      "message": "..." }
  { "type": "RATE_LIMIT", "message": "..." }
"""
from __future__ import annotations
import asyncio
import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas import CoachRequest
from app.websocket.manager import manager
from app.cache.ast_cache import get_cached_hint, set_cached_hint
from app.rate_limit.limiter import check_rate_limit
from app.utils.hashing import compute_request_hash
from app.db.database import AsyncSessionLocal
from app.db.crud import get_problem_by_slug, get_complexity_for_tier
from app.vector.qdrant_store import store_hint, search_similar_hints
from app.llm.agent import stream_agent_response

router = APIRouter()


async def _get_problem_context(req: CoachRequest) -> dict | None:
    """Fetch problem metadata + complexity target for the chosen tier from DB."""
    try:
        async with AsyncSessionLocal() as db:
            problem = await get_problem_by_slug(db, req.problem_slug)
            if not problem:
                return None

            tier = req.selected_tier or "OPTIMAL"
            ct = next(
                (t for t in problem.complexity_targets if t.tier == tier),
                None
            )
            return {
                "title":      problem.title,
                "difficulty": problem.difficulty,
                "category":   problem.category,
                "tier":       tier,
                "time_complexity":  ct.time_complexity  if ct else "?",
                "space_complexity": ct.space_complexity if ct else "?",
                "approach_name":    ct.approach_name    if ct else "",
                "description":      ct.description      if ct else "",
            }
    except Exception as exc:
        print(f"[Router] DB lookup failed: {exc}")
        return None


@router.websocket("/ws/coach")
async def coach_websocket(websocket: WebSocket):
    await websocket.accept()
    conn_id = manager.connect(websocket)

    try:
        while True:
            # ── 1. Receive + validate ────────────────────────────────────────
            raw = await websocket.receive_text()
            try:
                req = CoachRequest(**json.loads(raw))
            except (json.JSONDecodeError, ValidationError) as exc:
                await websocket.send_json({"type": "ERROR", "message": str(exc)})
                continue

            # ── 2. Rate limit ────────────────────────────────────────────────
            allowed, count = await check_rate_limit(conn_id)
            if not allowed:
                await websocket.send_json({
                    "type": "RATE_LIMIT",
                    "message": f"Rate limit exceeded ({count} requests). Please wait.",
                    "retry_after": 60,
                })
                continue

            # ── 3. Hash ──────────────────────────────────────────────────────
            req_hash = compute_request_hash(req)

            # ── 4. Cache lookup ──────────────────────────────────────────────
            cached_text = await get_cached_hint(req_hash)
            if cached_text:
                await websocket.send_json({"type": "CACHE_HIT", "cached": True})
                for i, word in enumerate(cached_text.split(" ")):
                    token = word if i == len(cached_text.split(" ")) - 1 else word + " "
                    await websocket.send_json({"type": "TOKEN", "token": token})
                    await asyncio.sleep(0.015)
                await websocket.send_json({"type": "DONE"})
                continue

            # ── 5. Fetch problem context from DB ─────────────────────────────
            ctx = await _get_problem_context(req)
            if ctx:
                await websocket.send_json({
                    "type":       "PROBLEM_CTX",
                    "title":      ctx["title"],
                    "difficulty": ctx["difficulty"],
                    "tier_info": {
                        "tier":             ctx["tier"],
                        "time_complexity":  ctx["time_complexity"],
                        "space_complexity": ctx["space_complexity"],
                        "approach_name":    ctx["approach_name"],
                    },
                })

            # ── 6. Stream from LangGraph Agent ───────────────────────────────
            full_parts: list[str] = []
            async for token in stream_agent_response(req, context=ctx):
                await websocket.send_json({"type": "TOKEN", "token": token})
                full_parts.append(token)

            full_text = "".join(full_parts)

            # ── 7. Cache + store in Qdrant ───────────────────────────────────
            if full_text.strip():
                await set_cached_hint(req_hash, full_text)
                try:
                    store_hint(
                        point_id=req_hash,
                        text=full_text,
                        problem_slug=req.problem_slug,
                        tier=req.selected_tier or "OPTIMAL",
                        hint_level=req.hint_level,
                    )
                except Exception:
                    pass  # Qdrant store failure is non-fatal

            # ── 8. Done ──────────────────────────────────────────────────────
            await websocket.send_json({"type": "DONE"})

    except WebSocketDisconnect:
        manager.disconnect(conn_id)
    except Exception as exc:
        print(f"[WS] Error on {conn_id}: {exc}")
        try:
            await websocket.send_json({"type": "ERROR", "message": "Internal server error."})
        except Exception:
            pass
        manager.disconnect(conn_id)
