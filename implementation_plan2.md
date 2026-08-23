# Phase 2: FastAPI WebSocket Gateway

## Goal
Stand up a production-grade FastAPI backend with:
- Async WebSocket endpoint the Chrome extension connects to
- AST-hash-based Redis caching (same code → same hint, no redundant LLM calls)
- Per-connection rate limiting (10 req/min)
- Streaming token protocol proven end-to-end with a stub LLM response
- Ready to plug LangGraph into in Phase 4

---

## Proposed Structure

```
backend/
├── app/
│   ├── main.py              ← FastAPI app, lifespan, CORS
│   ├── config.py            ← Pydantic Settings (env vars)
│   ├── schemas.py           ← CoachRequest / StreamToken Pydantic models
│   ├── websocket/
│   │   ├── router.py        ← ws://localhost:8000/ws/coach  endpoint
│   │   └── manager.py       ← ConnectionManager (active connections registry)
│   ├── cache/
│   │   ├── redis_client.py  ← Async Redis pool (redis-py asyncio)
│   │   └── ast_cache.py     ← get/set cached hint by AST hash
│   ├── rate_limit/
│   │   └── limiter.py       ← Sliding-window rate limiter via Redis
│   └── utils/
│       └── hashing.py       ← SHA-256 of (slug + action + tier + ast_summary)
├── requirements.txt
├── .env.example
└── run.py                   ← `uvicorn app.main:app --reload`
```

---

## WebSocket Protocol

### Client → Server (JSON)
```json
{
  "problem_slug": "two-sum",
  "action": "HINT",          // or "UPGRADE"
  "hint_level": 1,           // 1 | 2 | 3 | null for UPGRADE
  "selected_tier": "OPTIMAL",
  "ast_summary": { "loopDepth": 1, "nodeCount": 47, ... },
  "code_text": "def twoSum(...):"
}
```

### Server → Client (streaming)
```json
// Streamed tokens (one per message):
{ "type": "TOKEN", "token": "Your " }
{ "type": "TOKEN", "token": "loop " }
...
// Cache hit header:
{ "type": "CACHE_HIT", "cached": true }
// Terminal event:
{ "type": "DONE" }
// Error:
{ "type": "ERROR", "message": "Rate limit exceeded" }
```

---

## Redis Schema

| Key | Value | TTL |
|---|---|---|
| `coach:cache:{hash}` | Full hint text (string) | 1 hour |
| `coach:rate:{conn_id}` | Request count (int) | 60 seconds sliding window |

**Hash** = `SHA256(slug + action + hint_level + tier + ast_loopDepth + ast_nodeCount)`
(Captures problem + intent + code structure without storing raw code)

---

## Key Files

### [NEW] `app/main.py`
- FastAPI with `lifespan` context (Redis pool init/shutdown)
- CORS middleware allowing `chrome-extension://` origins
- Includes WebSocket router

### [NEW] `app/schemas.py`
- `ASTSummary` model
- `CoachRequest` model (validates incoming WS payload)

### [NEW] `app/websocket/router.py`
- `@router.websocket("/ws/coach")` endpoint
- On each message: validate → check rate limit → check cache → stream stub/LLM → cache result

### [NEW] `app/cache/ast_cache.py`
- `get_cached_hint(hash) -> str | None`
- `set_cached_hint(hash, text, ttl=3600)`

### [NEW] `app/rate_limit/limiter.py`
- `check_rate_limit(conn_id) -> bool`
- Uses Redis INCR + EXPIRE for sliding window

### [MODIFY] `extension/src/content/wsClient.js`
- Implement reconnect with exponential backoff
- Handle `CACHE_HIT` event (show ⚡ cached indicator in UI)

---

## Verification Plan

### Automated
```bash
# In backend/
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Test WebSocket manually
python -c "
import asyncio, websockets, json
async def test():
    async with websockets.connect('ws://localhost:8000/ws/coach') as ws:
        await ws.send(json.dumps({'problem_slug':'two-sum','action':'HINT','hint_level':1,'selected_tier':'OPTIMAL','ast_summary':{'loopDepth':1,'nodeCount':47},'code_text':''}))
        async for msg in ws:
            print(msg)
asyncio.run(test())
"
```

### Manual E2E
- Load extension → navigate to LeetCode Two Sum
- Select OPTIMAL → click Hint L1
- Observe tokens streaming into the panel
- Click Hint L1 again → observe CACHE_HIT (instant response)
- Click 11+ times → observe rate limit error in panel

---

## Open Questions

> [!IMPORTANT]
> **Redis**: Do you have Redis installed locally, or should I use a Docker container?
> I can provide a `docker-compose.yml` with Redis + the backend together.

> [!NOTE]
> **LLM key**: Phase 2 uses a **stub streamer** (no real LLM) to prove the protocol.
> The real Claude/GPT call plugs in Phase 4. You can set `LLM_PROVIDER=stub` in `.env`.
