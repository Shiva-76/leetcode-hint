"""
main.py — FastAPI application entry point.

Lifecycle:
  startup  → connect Redis pool
  shutdown → close Redis pool

Routes:
  GET  /health       → health check (Redis ping)
  WS   /ws/coach     → coaching WebSocket
"""
from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.cache.redis_client import init_redis, close_redis, get_redis
from app.websocket.router import router as ws_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup / shutdown side-effects."""
    # ── Startup ───────────────────────────────────────────────────────────────
    print("[App] Starting up...")
    await init_redis()
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    print("[App] Shutting down...")
    await close_redis()


app = FastAPI(
    title="LeetCode Algo Coach API",
    description="Adaptive AST-Based Algorithmic Coach — WebSocket Gateway",
    version="2.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Allow Chrome extension origins (chrome-extension://*) + localhost for dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tightened in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(ws_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    """Returns OK if FastAPI is running and Redis is reachable."""
    from app.cache.redis_client import is_redis_available, get_redis
    if is_redis_available():
        try:
            await get_redis().ping()
            redis_status = "ok"
        except Exception as exc:
            redis_status = f"error: {exc}"
    else:
        redis_status = "unavailable (run: docker compose up -d)"

    return {
        "status": "ok",
        "redis": redis_status,
        "env": settings.app_env,
        "llm_provider": settings.llm_provider,
    }
