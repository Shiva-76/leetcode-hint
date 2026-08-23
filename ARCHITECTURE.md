# Adaptive AST-Based Algorithmic Coach — Build Journal

> **Living document** — updated after every phase.
> Explains every architectural decision, tool choice, connection, and implementation detail.

---

## Table of Contents

- [Project Vision](#project-vision)
- [Full Architecture Overview](#full-architecture-overview)
- [Tech Stack](#tech-stack)
- [Phase 1 — Chrome Extension & WebAssembly AST Parser](#phase-1--chrome-extension--webassembly-ast-parser)
- [Phase 2 — FastAPI WebSocket Gateway](#phase-2--fastapi-websocket-gateway)
- [How Phase 1 and Phase 2 Connect](#how-phase-1-and-phase-2-connect)
- [Running the Project](#running-the-project)
- [Phases Ahead](#phases-ahead)

---

## Project Vision

A **Chrome Extension** that sits inside LeetCode and acts as an AI-powered algorithmic coach. Instead of just giving answers, it uses **Progressive Socratic Hints** — three levels of hints that nudge the user to think deeper rather than just copy a solution.

The coach:
1. **Reads the user's code** in real-time using a WebAssembly AST parser
2. **Understands its structure** (loop depth, nesting, node count)
3. **Routes that analysis** to a backend AI that evaluates the code against the problem's optimal solution
4. **Streams hints back** word-by-word, like a real tutor thinking aloud
5. **Caches responses** so the same structural code pattern never hits the LLM twice

---

## Full Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Chrome Extension (MV3)                   │
│                                                             │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │ Service Worker  │    │   Content Script             │   │
│  │ (background)    │    │                              │   │
│  │                 │    │  ┌────────────────────────┐  │   │
│  │ • Tab tracking  │    │  │  web-tree-sitter (WASM) │  │   │
│  │ • Slug detect   │◄───┤  │  AST Parser            │  │   │
│  │ • SPA nav relay │    │  │  • Python grammar       │  │   │
│  └─────────────────┘    │  │  • C++ grammar          │  │   │
│                         │  │  • Loop depth calc      │  │   │
│                         │  └────────────────────────┘  │   │
│                         │                              │   │
│                         │  ┌────────────────────────┐  │   │
│                         │  │  Shadow DOM + React UI  │  │   │
│                         │  │  • StrategyDropdown     │  │   │
│                         │  │  • HintButtons (L1/2/3) │  │   │
│                         │  │  • UpgradeButton        │  │   │
│                         │  │  • ResponseDisplay      │  │   │
│                         │  └────────────────────────┘  │   │
│                         │                              │   │
│                         │  ┌────────────────────────┐  │   │
│                         │  │  wsClient.js            │  │   │
│                         │  │  • WebSocket connect    │  │   │
│                         │  │  • Exponential backoff  │  │   │
│                         │  │  • Token stream handler │  │   │
│                         │  └──────────┬─────────────┘  │   │
│                         └────────────┼─────────────────┘   │
└──────────────────────────────────────┼─────────────────────┘
                                       │ ws://localhost:8000/ws/coach
                                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│                                                             │
│  WebSocket Router (/ws/coach)                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  1. Parse + Validate (Pydantic CoachRequest)         │  │
│  │  2. Rate Limit check (INCR+EXPIRE in Redis/Memory)   │  │
│  │  3. SHA-256 Hash (slug+action+tier+ast_structure)    │  │
│  │  4. Cache Lookup → HIT: stream cached text           │  │
│  │  5. Cache MISS → LangGraph pipeline (Phase 4)        │  │
│  │              → Stub streamer (Phase 2)               │  │
│  │  6. Cache the full response                          │  │
│  │  7. Send DONE                                        │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                             │
│  ┌─────────────┐  ┌────────────────┐  ┌─────────────────┐  │
│  │ Redis /     │  │  PostgreSQL    │  │  Qdrant         │  │
│  │ MemoryStore │  │  (Phase 3)     │  │  Vector DB      │  │
│  │ • Cache     │  │  • Problems    │  │  (Phase 3)      │  │
│  │ • RateLimit │  │  • Complexity  │  │  • Embeddings   │  │
│  └─────────────┘  └────────────────┘  └─────────────────┘  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ LangGraph AI Agent (Phase 4)                         │  │
│  │ - Framework: LangGraph + LangChain.                  │  │
│  │ - Embeddings: fastembed (BAAI/bge-small-en-v1.5).    │  │
│  │ - Nodes: retrieve_context, generate_hint,            │  │
│  │   evaluate_upgrade.                                  │  │
│  │ - Provider: Agnostic (Claude 3.5 Sonnet / GPT-4o).   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Extension framework | Chrome MV3 | Required for modern Chrome extensions |
| Extension bundler | Vite + CRXJS | Fast HMR, handles MV3 quirks automatically |
| Extension UI | React 18 | Component model, hooks for state |
| CSS isolation | Shadow DOM + Tailwind (`lc-` prefix) | Prevents LeetCode's CSS from leaking in |
| Code parser | `web-tree-sitter` (WASM) | Runs in-browser, no server round-trip for AST |
| Backend | FastAPI (Python 3.14) | Async-native, automatic OpenAPI docs, WebSocket support |
| WebSocket server | Uvicorn with `standard` extras | Production-grade ASGI, httptools + uvloop |
| Data validation | Pydantic v2 | Fast, type-safe, great error messages |
| Caching | Redis 8 / MemoryStore fallback | Sub-millisecond cache hits, same API either way |
| Rate limiting | Redis INCR+EXPIRE pattern | Atomic, TTL-based sliding window |
| Cache key | SHA-256 of request semantics | Structurally equivalent code → same cache hit |
| AI orchestration | LangGraph (Phase 4) | Stateful DAG for multi-step hint generation |
| LLM | Claude 3.5 Sonnet / GPT-4o | Configurable via `LLM_PROVIDER` env var |
| Database | PostgreSQL + SQLAlchemy async (Phase 3) | Problem metadata, complexity targets |
| Vector search | Qdrant (Phase 3) | Semantic similarity for hint retrieval |

---

## Phase 1 — Chrome Extension & WebAssembly AST Parser

### What we built
A fully functional Chrome Extension (Manifest V3) that:
- Injects a floating, draggable coaching panel into any `leetcode.com/problems/*` page
- Detects the current problem slug from the URL
- Parses the user's code using a WebAssembly AST engine
- Tracks navigation between problems without page reloads (SPA-aware)

### Directory structure
```
extension/
├── manifest.json                    ← MV3 manifest
├── package.json                     ← Node.js project config
├── vite.config.js                   ← Vite + CRXJS build pipeline
├── tailwind.config.js               ← Tailwind with lc- prefix
├── postcss.config.js                ← PostCSS for Tailwind processing
├── public/
│   ├── icons/                       ← icon16/48/128.png (generated)
│   └── wasm/tree-sitter.wasm        ← core WASM parser engine
├── scripts/
│   └── create-icons.mjs             ← Icon generator (no external deps)
└── src/
    ├── background/service-worker.js ← Background service worker
    ├── content/
    │   ├── index.jsx                ← Content script entry + Shadow DOM
    │   ├── ASTParser.js             ← web-tree-sitter wrapper
    │   └── wsClient.js              ← WebSocket client
    ├── panel/
    │   ├── App.jsx                  ← Main React panel component
    │   ├── index.css                ← Tailwind CSS (bundled inline)
    │   └── components/
    │       ├── StrategyDropdown.jsx ← BRUTE_FORCE / BETTER / OPTIMAL
    │       ├── HintButtons.jsx      ← L1 / L2 / L3 progressive unlock
    │       ├── UpgradeButton.jsx    ← Code upgrade evaluator
    │       └── ResponseDisplay.jsx ← Streaming markdown renderer
    └── shims/
        └── empty.js                ← Node.js built-in shims for browser
```

### Step-by-step: How the extension works

#### Step 1 — Build pipeline
We use **Vite + CRXJS** (`@crxjs/vite-plugin`). CRXJS reads `manifest.json` and automatically:
- Bundles content scripts into the format Chrome expects
- Handles service worker registration
- Copies public assets (icons, wasm) to `dist/`

**Problem encountered:** `vite-plugin-static-copy` requires `type: "module"` in `package.json` — added it.
**Problem encountered:** `import assert { type: 'json' }` is deprecated in Node 24 — changed to `import with { type: 'json' }`.

#### Step 2 — Manifest V3 structure
```json
{
  "manifest_version": 3,
  "content_scripts": [{ "matches": ["*://leetcode.com/problems/*"] }],
  "background": { "service_worker": "src/background/service-worker.js" },
  "web_accessible_resources": [{ "resources": ["wasm/*"] }]
}
```

The content script only runs on `leetcode.com/problems/*` — not on every page.

#### Step 3 — Service Worker (background script)
`service-worker.js` listens to `chrome.tabs.onUpdated`:

```javascript
// Fires on BOTH full page loads AND SPA URL changes
const url = changeInfo.url || (changeInfo.status === 'complete' ? tab.url : null);
const match = url.match(/leetcode\.com\/problems\/([^/]+)/);
if (match) {
    chrome.tabs.sendMessage(tabId, { type: 'SLUG_DETECTED', slug: match[1] });
}
```

**Key insight:** LeetCode is a React SPA. When you navigate from "Two Sum" to "Median of Two Sorted Arrays", there's no page reload — Chrome still fires `tabs.onUpdated` with `changeInfo.url` for pushState navigations.

#### Step 4 — Content Script + Shadow DOM injection
`src/content/index.jsx` is the entry point that runs in the page context:

```javascript
// 1. Create a host element fixed to viewport
const hostEl = document.createElement('div');
hostEl.style.cssText = 'position:fixed;top:0;left:0;z-index:2147483647;pointer-events:none;';
document.documentElement.appendChild(hostEl);

// 2. Attach shadow DOM for CSS isolation
const shadow = hostEl.attachShadow({ mode: 'open' });

// 3. Inject Tailwind CSS as a <style> tag (NOT a <link> — that doesn't work in shadow DOM)
import panelCSS from '../panel/index.css?inline';  // Vite ?inline bundles CSS as string
const styleEl = document.createElement('style');
styleEl.textContent = panelCSS;
shadow.appendChild(styleEl);

// 4. Mount React into the shadow DOM
const root = createRoot(mountEl);
root.render(<App mountEl={mountEl} />);
```

**Why Shadow DOM?** LeetCode has its own CSS that would override our panel styles. Shadow DOM creates a completely isolated style scope.

**Why `?inline`?** A `<link rel="stylesheet">` inside shadow DOM can't load extension URLs due to browser security restrictions. Vite's `?inline` suffix bundles the entire CSS file as a JavaScript string at build time, which we then inject as a `<style>` tag.

#### Step 5 — SPA Navigation Detection (3 layers)

```javascript
// Layer 1: Intercept history.pushState/replaceState (React Router uses these)
history.pushState = function(...args) { _push(...args); handleURLChange(); };
history.replaceState = function(...args) { _replace(...args); handleURLChange(); };

// Layer 2: Handle browser back/forward
window.addEventListener('popstate', handleURLChange);

// Layer 3: Service worker message relay (backup for full page loads)
chrome.runtime.onMessage.addListener((msg) => {
    if (msg.type === 'SLUG_DETECTED') notifySlugChange(msg.slug);
});

function handleURLChange() {
    const newSlug = getSlugFromURL();  // /problems/([^/?#]+)/
    if (newSlug !== currentSlug) {
        currentSlug = newSlug;
        mountEl.dispatchEvent(new CustomEvent('lc-slug-change', { detail: { slug: newSlug } }));
    }
}
```

When `lc-slug-change` fires, React's `App.jsx` resets all state — strategy, hints, response, AST — for the new problem.

#### Step 6 — WebAssembly AST Parser
`ASTParser.js` uses `web-tree-sitter`:

```javascript
// Lazy initialization (doesn't block page load)
await TreeSitter.init();  // loads tree-sitter.wasm
// Language grammars (tree-sitter-python.wasm) are downloaded at runtime

// Attaches a MutationObserver to Monaco editor DOM
// When the editor content changes → re-parse and extract:
const astSummary = {
    language: 'python',
    nodeCount: tree.rootNode.descendantCount,
    loopDepth: calculateMaxLoopDepth(tree.rootNode),
    hasNestedLoops: loopDepth >= 2,
    loops: [...],       // all loop node positions
    functions: [...]    // all function definitions
};
```

**loopDepth** is the key metric: O(N²) code has `loopDepth: 2`, O(N) code has `loopDepth: 1`.

#### Step 7 — React Panel UI

The panel is draggable (mouse drag on header), collapsible (collapse button), and has:

- **StrategyDropdown** — pick Brute Force / Better / Optimal tier
- **HintButtons** — L1, L2, L3 with progressive unlock (must request L1 before L2, etc.)
- **UpgradeButton** — evaluates code against next tier
- **ResponseDisplay** — renders streaming markdown with a skeleton shimmer while loading

All state resets automatically on problem navigation via the `lc-slug-change` event.

#### Step 8 — Icon generation
Since we had no design tools, we wrote `scripts/create-icons.mjs` — a pure Node.js script using only `zlib` and `fs` built-ins that generates valid PNG files (16×16, 48×48, 128×128) with an indigo background and "AI" glyph. No npm packages needed.

#### Key decisions and tradeoffs

| Decision | Alternative | Reason |
|---|---|---|
| Shadow DOM | iframe | iframe has same-origin restrictions; shadow DOM is simpler |
| CSS `?inline` import | `<link>` tag | `<link>` tags can't load extension URLs from shadow DOM |
| `history.pushState` intercept | `MutationObserver` on URL | More reliable; fires synchronously on navigation |
| No hardcoded complexity labels | Show O(N²) etc. | Each problem has unique complexity; DB provides these in Phase 3 |
| CRXJS plugin | Custom Rollup config | CRXJS handles MV3 quirks (service worker, web-accessible-resources) automatically |

---

## Phase 2 — FastAPI WebSocket Gateway

### What we built
A production-grade Python backend that:
- Accepts WebSocket connections from the Chrome extension
- Validates every message with Pydantic v2 schemas
- Enforces per-connection rate limits
- Computes a semantic cache key from the request (not raw code)
- Returns cached responses instantly when the same code structure is seen again
- Streams hint text token-by-token (simulating LLM output)
- Degrades gracefully: works without Docker/Redis using an in-process MemoryStore

### Directory structure
```
backend/
├── .env                              ← Local config (not committed to git ideally)
├── .env.example                      ← Template for new developers
├── requirements.txt                  ← Python dependencies
├── run.py                            ← Uvicorn entry point
├── test_websocket.py                 ← E2E test (13/13 passing)
└── app/
    ├── main.py                       ← FastAPI app + lifespan + CORS
    ├── config.py                     ← Pydantic Settings (reads .env)
    ├── schemas.py                    ← CoachRequest + all message types
    ├── cache/
    │   ├── redis_client.py           ← Auto-selects Redis or MemoryStore
    │   ├── memory_store.py           ← Pure-Python Redis-compatible fallback
    │   └── ast_cache.py              ← get/set hint text by hash
    ├── rate_limit/
    │   └── limiter.py                ← INCR+EXPIRE sliding window
    ├── utils/
    │   └── hashing.py                ← SHA-256 semantic cache key
    ├── websocket/
    │   ├── manager.py                ← ConnectionManager (UUID per connection)
    │   └── router.py                 ← @router.websocket("/ws/coach")
    └── llm/
        └── stub_streamer.py          ← Fake streaming (→ LangGraph in Phase 4)
```

### Step-by-step: How the backend works

#### Step 1 — Dependency installation

**Problem:** User has Python 3.14 (very new). `pydantic-core 2.27.1` had no pre-built wheel for Python 3.14 (cp314) and required Rust + MSVC linker to compile — which weren't installed.

**Solution:** Install `fastapi[standard]` without version pinning. pip automatically resolved `pydantic-core 2.46.4` which **does** have a pre-built cp314 wheel:

```
pydantic-core-2.46.4-cp314-cp314-win_amd64.whl  ← pre-built, no compilation
```

**Lesson:** Never hard-pin `pydantic-core` — let pip resolve it against the Python version.

#### Step 2 — FastAPI app with lifespan

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[App] Starting up...")
    await init_redis()      # Try Redis → fall back to MemoryStore
    yield                   # App runs here
    print("[App] Shutting down...")
    await close_redis()     # Clean up

app = FastAPI(lifespan=lifespan)
```

**Why lifespan?** The old `@app.on_event("startup")` is deprecated in FastAPI. The lifespan context manager is the modern pattern — it cleanly pairs startup and shutdown.

#### Step 3 — Pydantic v2 schemas

```python
class ASTSummary(BaseModel):
    language: str = "unknown"
    node_count: int = Field(0, alias="nodeCount")    # camelCase from JS
    loop_depth: int = Field(0, alias="loopDepth")
    has_nested_loops: bool = Field(False, alias="hasNestedLoops")
    model_config = {"populate_by_name": True}        # accept both styles

class CoachRequest(BaseModel):
    problem_slug: str
    action: Literal["HINT", "UPGRADE"]
    hint_level: Optional[Literal[1, 2, 3]] = None
    selected_tier: Optional[Literal["BRUTE_FORCE", "BETTER", "OPTIMAL"]] = None
    ast_summary: Optional[ASTSummary] = None
    code_text: str = ""
```

**Key design:** `ASTSummary` uses `alias` for camelCase fields because JavaScript sends `nodeCount`, but Python convention is `node_count`. Pydantic handles both.

#### Step 4 — Redis / MemoryStore auto-detection

```python
async def init_redis():
    try:
        pool = aioredis.from_url(settings.redis_url, ...)
        await pool.ping()           # Actually test the connection
        _store = pool               # Real Redis available
        print("Redis connected")
    except Exception:
        _store = MemoryStore()      # Fall back transparently
        print("Using in-memory store")
```

**MemoryStore** implements the exact same async API (`get`, `setex`, `incr`, `expire`, `aclose`, `ping`) using a Python dict + TTL timestamps. All callers use `get_redis()` and never know which backend they're using.

```python
# MemoryStore.incr — atomic because Python's GIL + asyncio
async def incr(self, key: str) -> int:
    current = int(self._data.get(key, 0))
    self._data[key] = str(current + 1)
    return current + 1
```

#### Step 5 — Semantic cache key

```python
def compute_request_hash(req: CoachRequest) -> str:
    key_data = {
        "slug":       req.problem_slug,      # WHICH problem
        "action":     req.action,            # HINT or UPGRADE
        "hint_level": req.hint_level,        # L1/L2/L3
        "tier":       req.selected_tier,     # BRUTE_FORCE/BETTER/OPTIMAL
        "loop_depth": req.ast_summary.loop_depth,   # code STRUCTURE
        "node_count": req.ast_summary.node_count,   # code SIZE
    }
    return hashlib.sha256(json.dumps(key_data, sort_keys=True).encode()).hexdigest()
```

**Why not hash the raw code?** If the user renames a variable, the code changes but the algorithm doesn't. We hash the **structural semantics** — same structure → same hint → same cache hit. This dramatically improves cache hit rates.

#### Step 6 — WebSocket pipeline (7 steps)

```python
@router.websocket("/ws/coach")
async def coach_websocket(websocket: WebSocket):
    await websocket.accept()
    conn_id = manager.connect(websocket)  # UUID assigned
    try:
        while True:
            raw = await websocket.receive_text()

            # 1. Validate
            req = CoachRequest(**json.loads(raw))

            # 2. Rate limit (10 req/min per connection)
            allowed, count = await check_rate_limit(conn_id)
            if not allowed:
                await websocket.send_json({"type": "RATE_LIMIT", ...})
                continue

            # 3. Hash
            req_hash = compute_request_hash(req)

            # 4. Cache check
            cached = await get_cached_hint(req_hash)
            if cached:
                await websocket.send_json({"type": "CACHE_HIT", "cached": True})
                for word in cached.split(" "):
                    await websocket.send_json({"type": "TOKEN", "token": word + " "})
                    await asyncio.sleep(0.015)   # natural feel even from cache
                await websocket.send_json({"type": "DONE"})
                continue

            # 5. Stream from LLM/stub
            full_text = []
            async for token in stream_stub_response(req):
                await websocket.send_json({"type": "TOKEN", "token": token})
                full_text.append(token)

            # 6. Cache result
            await set_cached_hint(req_hash, "".join(full_text))

            # 7. Done
            await websocket.send_json({"type": "DONE"})

    except WebSocketDisconnect:
        manager.disconnect(conn_id)
```

#### Step 7 — Stub LLM streamer

The stub returns pre-written Socratic hints per (action, hint_level). It streams word-by-word with 50ms delays to simulate real LLM token generation:

```python
STUB_HINTS = {
    ("HINT", 1): "Your loop iterates through every pair — but do you **really** need to check *both* elements...",
    ("HINT", 2): "Let's trace through nums = [2,7,11,15], target=9:\n- Outer i=0 → nums[0]=2...",
    ("HINT", 3): "Your approach uses nested loops → O(N²).\n\nThe key insight: for each nums[i]..."
}

async def stream_stub_response(req):
    text = STUB_HINTS.get(("HINT", req.hint_level), fallback)
    for i, word in enumerate(text.split(" ")):
        yield word + " "
        await asyncio.sleep(0.05)  # 50ms per token → ~20 tokens/sec
```

In Phase 4, this async generator gets replaced by a LangGraph streaming call — same interface, real AI.

#### Step 8 — E2E verification

```
[1] Health Check
  [PASS] status == ok
  [PASS] redis field  (MemoryStore active)
  [PASS] llm_provider  (stub)

[2] HINT L1 — Token streaming
  [PASS] got TOKEN messages  (28 tokens)
  [PASS] ends with DONE
  [PASS] no ERROR in stream
  [PASS] text len > 20 chars  (168 chars)
     Preview: Your loop iterates through every pair...

[3] Cache Hit — same request again
  [PASS] CACHE_HIT received        ← instant, no LLM call
  [PASS] tokens still stream
  [PASS] ends with DONE

[4] UPGRADE action
  [PASS] got TOKEN messages
  [PASS] ends with DONE

[5] Invalid payload -> ERROR (no crash)
  [PASS] ERROR returned

====================================================
  13/13 checks passed -- ALL GOOD!
====================================================
```

#### Step 9 — Windows-specific issues resolved

| Problem | Cause | Fix |
|---|---|---|
| `UnicodeEncodeError` on startup | Windows terminal uses cp1252, not UTF-8; emoji in print() crashed | Set `PYTHONUTF8=1` env var; removed emoji from print statements |
| `pydantic-core` build failure | Python 3.14 had no pre-built wheel; Rust compilation needs MSVC | Used `fastapi[standard]` without version pin; pip found cp314 wheel |
| `redis[asyncio]` warning | redis 8.x doesn't have `asyncio` as a named extra anymore | Use `redis` (asyncio is built-in to redis-py 5+) |

### WebSocket message protocol

```
CLIENT → SERVER:
{
  "problem_slug": "two-sum",
  "action": "HINT" | "UPGRADE",
  "hint_level": 1 | 2 | 3 | null,
  "selected_tier": "BRUTE_FORCE" | "BETTER" | "OPTIMAL",
  "ast_summary": { "nodeCount": 47, "loopDepth": 2, "hasNestedLoops": true },
  "code_text": "def twoSum(...):"
}

SERVER → CLIENT (streaming):
{ "type": "TOKEN",      "token": "Your "    }  ← one per word
{ "type": "TOKEN",      "token": "loop "    }
...
{ "type": "CACHE_HIT",  "cached": true      }  ← only on cache hits
{ "type": "DONE"                            }  ← always last
{ "type": "ERROR",      "message": "..."    }  ← validation errors
{ "type": "RATE_LIMIT", "message": "...", "retry_after": 60 }
```

---

## How Phase 1 and Phase 2 Connect

```
LeetCode Page
     │
     │ User types code in Monaco editor
     ▼
ASTParser.js (MutationObserver on Monaco DOM)
     │
     │ Extracts { loopDepth, nodeCount, hasNestedLoops }
     │ Fires CustomEvent('lc-ast-update') on mountEl
     ▼
App.jsx (React, inside Shadow DOM)
     │
     │ User selects "OPTIMAL" + clicks "Hint L1"
     ▼
wsClient.js
     │
     │ sendPayload({ problem_slug, action, hint_level, selected_tier, ast_summary, code_text })
     │ WebSocket send → ws://localhost:8000/ws/coach
     ▼
FastAPI WebSocket Router
     │
     │ Validates → Rate limits → Hashes → Cache check → Stream
     ▼
stub_streamer.py (Phase 2) / LangGraph (Phase 4)
     │
     │ Yields tokens async
     ▼
WebSocket sends { type: "TOKEN", token: "..." } × N
     │
     │ Chrome receives each message
     ▼
wsClient.js → CustomEvent('lc-ws-message') → App.jsx → setResponse(prev + token)
     │
     ▼
ResponseDisplay.jsx renders streaming markdown in real-time
```

---

## Running the Project

### Prerequisites
- Python 3.11+ (3.14 works) with `.venv`
- Node.js 18+ (24 works)

### 1. Start the backend
```powershell
# From repo root
$env:PYTHONUTF8 = "1"
& ".venv\Scripts\python.exe" backend\run.py
# → Server starts at http://localhost:8000
# → MemoryStore active (no Redis/Docker needed)
```

### 2. Enable real Redis (optional, when Docker is available)
```bash
docker compose up -d
# redis_client.py auto-detects and switches to real Redis
```

### 3. Build the extension
```powershell
cd extension
npm install    # first time only
npm run build  # outputs to extension/dist/
```

### 4. Load in Chrome
1. Open `chrome://extensions`
2. Enable **Developer Mode**
3. Click **Load unpacked** → select `extension/dist/`
4. Navigate to any `leetcode.com/problems/*` page

### 5. Run E2E tests
```powershell
# With server running:
$env:PYTHONUTF8 = "1"
& ".venv\Scripts\python.exe" backend\test_websocket.py
```

---

## Phases Ahead

| Phase | What | Key Technologies |
|---|---|---|
| - [x] | **Phase 1**: Chrome Extension setup (Shadow DOM, React, WebSocket client, AST basic setup) | React, CRXJS, web-tree-sitter WASM |
| - [x] | **Phase 2**: Python backend skeleton (FastAPI, WebSockets, Rate limiting, Redis-lite) | FastAPI, Pydantic v2, Redis/MemoryStore |
| - [x] | **Phase 3**: DB & Vector Store (PostgreSQL/SQLite, ORM, Qdrant setup) | SQLAlchemy, Qdrant |
| - [x] | **Phase 4**: LangGraph Agent (Socratic prompts, Claude/OpenAI wiring) | LangGraph, LangChain, Claude/GPT-4o |
| - [ ] | **Phase 5**: Polish, Auth, and final E2E testing | Full integration, auth, production config |

---

## Phase 3 — Database & Vector Search

### What we built
- **Database Layer**: SQLAlchemy asynchronous configuration with fallback (`SQLite` by default, easily swapped to `PostgreSQL`).
- **Models & CRUD**: Designed `Problem` and `ComplexityTarget` models to link 1-to-many complexity targets for each problem tier (Brute Force, Better, Optimal).
- **Qdrant Vector Store**: Embedded a lightweight, in-memory instance of `Qdrant` into the FastAPI startup to cache hints deterministically based on SHA-256 (will serve semantic similarity in Phase 4).
- **Data Seeding**: Written a robust `seed.py` that populates 54 popular LeetCode questions containing accurate time/space complexities alongside approach names.
- **WebSocket Context Hook**: The WebSocket router was augmented to pull the exact problem metadata and complexity target directly from the DB at runtime, embedding it in the Socratic Hint prefix.
- **Extension Update**: Updated `App.jsx` and `StrategyDropdown.jsx` to dynamically hit the new `/api/problems/{slug}` endpoint to show real-time complexity tags per strategy.
