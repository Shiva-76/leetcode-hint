"""
main.py — FastAPI application entry point.

Lifecycle:
  startup  → connect Redis/MemoryStore, init DB tables, seed problems, init Qdrant
  shutdown → close all connections

Routes:
  GET  /health              → health check
  GET  /api/problems/       → list seeded problems
  GET  /api/problems/{slug} → problem metadata + complexity targets
  WS   /ws/coach            → coaching WebSocket
"""
from __future__ import annotations
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.cache.redis_client import init_redis, close_redis, get_redis, is_redis_available
from app.db.database import init_db, close_db
from app.db.seed import run_seed
from app.vector.qdrant_store import init_qdrant, close_qdrant
from app.websocket.router import router as ws_router
from app.api.problems import router as problems_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    print("[App] Starting up...")
    await init_redis()
    await init_db()
    await run_seed()         # idempotent — skips existing problems
    init_qdrant()
    yield
    # ── Shutdown ──────────────────────────────────────────────────────────────
    print("[App] Shutting down...")
    await close_redis()
    await close_db()
    close_qdrant()


app = FastAPI(
    title="LeetCode Algo Coach API",
    description="Adaptive AST-Based Algorithmic Coach",
    version="3.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(ws_router)
app.include_router(problems_router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health_check():
    redis_status = "ok" if is_redis_available() else "in-memory fallback"
    return {
        "status":       "ok",
        "redis":        redis_status,
        "env":          settings.app_env,
        "llm_provider": settings.llm_provider,
        "database":     settings.database_url.split("://")[0],
        "qdrant":       "server" if settings.qdrant_url else "in-memory",
    }
