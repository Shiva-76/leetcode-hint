# LeetCode Algorithmic Coach — Full System Design Document

> **Type:** RAG-powered, LangGraph AI Agent • Chrome Extension • Production-ready Cloud System  
> **Status:** Phases 1–5 Complete | AWS EC2 Deployment Ready  
> **GitHub:** [Shiva-76/leetcode-hint](https://github.com/Shiva-76/leetcode-hint)

---

## 1. What Is This?

**LeetCode Algorithmic Coach** is a context-aware, real-time AI coaching system embedded directly into the LeetCode website as a Chrome Extension. It watches the user write code, deeply understands the structure of that code at the AST (Abstract Syntax Tree) level, and then invokes a multi-stage AI agent to deliver **Socratic algorithmic guidance** — guiding the user to the optimal solution through questions and nudges, rather than just handing them the answer.

It is fundamentally a **Generative AI application** that combines:
- **In-browser code intelligence** (WebAssembly AST parsing)
- **Real-time bidirectional communication** (WebSockets)
- **Agentic LLM orchestration** (LangGraph)
- **Retrieval-Augmented Generation** (Qdrant Vector DB)
- **Semantic caching** (Redis + SHA-256 hashing)
- **Production containerized deployment** (Docker + AWS EC2)

---

## 2. High-Level System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                     BROWSER (Chrome Extension)                   │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Content Script (content/index.jsx)                       │  │
│  │                                                           │  │
│  │  ┌─────────────────────┐  ┌──────────────────────────┐   │  │
│  │  │  ASTParser.js       │  │  wsClient.js             │   │  │
│  │  │  tree-sitter (WASM) │  │  Auto-reconnect WS       │   │  │
│  │  │  MutationObserver   │  │  Exponential backoff     │   │  │
│  │  │  Monaco API         │  │  chrome.storage.local    │   │  │
│  │  │  Loop depth calc    │  │  Auth token injection    │   │  │
│  │  └────────┬────────────┘  └──────────┬───────────────┘   │  │
│  │           │ CustomEvents             │ WebSocket          │  │
│  │           ▼                          ▼                    │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  React Panel (panel/App.jsx) in Shadow DOM          │  │  │
│  │  │  Draggable, collapsible floating UI                 │  │  │
│  │  │  StrategyDropdown / HintButtons / ResponseDisplay   │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────────────────────┐                    │
│  │  Options Page (options/Options.jsx)     │                    │
│  │  Configure Backend URL + Auth Token     │                    │
│  │  Persisted in chrome.storage.local      │                    │
│  └─────────────────────────────────────────┘                    │
└──────────────────────────────────────────────────────────────────┘
                              │  WebSocket (ws://)
                              ▼
┌──────────────────────────────────────────────────────────────────┐
│                    BACKEND (FastAPI / Python)                    │
│                                                                  │
│   /ws/coach  8-Step WebSocket Pipeline:                         │
│   [1] JSON Parse + Pydantic Validation                          │
│   [2] Auth Token Verification                                   │
│   [3] Rate Limit (Redis Sliding Window)                         │
│   [4] SHA-256 Semantic Hash                                     │
│   [5] Redis Cache Lookup → HIT: stream cached tokens           │
│   [6] PostgreSQL Problem Context Fetch                          │
│   [7] LangGraph Agent → Stream LLM tokens                      │
│   [8] Store result in Redis + Qdrant                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  LangGraph Agent (llm/agent.py)                          │   │
│  │                                                          │   │
│  │  START → retrieve_context_node                           │   │
│  │             (Qdrant vector search via fastembed)         │   │
│  │                    │                                     │   │
│  │          [conditional_edge on action]                    │   │
│  │           │                        │                     │   │
│  │    generate_hint_node      evaluate_upgrade_node         │   │
│  │    HINT_SYSTEM_PROMPT      UPGRADE_SYSTEM_PROMPT         │   │
│  │    AST + Tier + RAG        AST + Code + Tier             │   │
│  │           │                        │                     │   │
│  │           └──────────┬─────────────┘                     │   │
│  │                      ▼                                   │   │
│  │              END (token stream)                          │   │
│  └──────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────┘
          │                    │                    │
          ▼                    ▼                    ▼
 ┌──────────────┐   ┌─────────────────┐   ┌──────────────────┐
 │  PostgreSQL  │   │  Redis          │   │  Qdrant          │
 │  problems    │   │  Hint cache     │   │  Vector store    │
 │  complexity  │   │  Rate limiting  │   │  coach_hints     │
 │  targets     │   │  TTL: 1 hour    │   │  384-dim cosine  │
 └──────────────┘   └─────────────────┘   └──────────────────┘
```

---

## 3. Component Deep-Dive

### 3.1 Chrome Extension (Frontend)

#### Layer 1: Content Script (`content/index.jsx`)
The entry point injected into every `leetcode.com/problems/*` page. It orchestrates the AST parser, the WebSocket client, and the React panel. It mounts the React UI into a **Shadow DOM** to prevent CSS conflicts with LeetCode's own styles.

#### Layer 2: AST Parser (`content/ASTParser.js`)
The most technically unique part of the frontend:
- Loads **WebAssembly grammar files** (`tree-sitter-python.wasm`, `tree-sitter-cpp.wasm`) at runtime via `chrome.runtime.getURL()`.
- Attaches a **`MutationObserver`** to Monaco Editor's DOM container with a 600ms debounce to detect every keystroke without hammering performance.
- Intercepts LeetCode's **Monaco editor instance** via `window.monaco.editor.getModels()` to extract raw code text — no fragile DOM scraping needed.
- Performs a full **syntax tree walk** to count nodes, detect loop types, calculate nesting depth, and extract function signatures.
- Computes **`loopDepth`** as a proxy for Big-O time complexity (0 = O(1), 1 = O(N), 2 = O(N²)).

**Output — ASTSummary sent to backend:**
```json
{
  "language": "python",
  "nodeCount": 143,
  "loopDepth": 2,
  "hasNestedLoops": true,
  "loops": [{"type": "for_statement", "line": 5, "nested": false}],
  "functions": [{"name": "twoSum", "line": 3}]
}
```

#### Layer 3: WebSocket Client (`content/wsClient.js`)
A production-grade, self-healing WebSocket client:
- **Lazy configuration**: Reads `backendUrl` and `authToken` from `chrome.storage.local` at the moment of connection. This enables the Options page to reconfigure the extension without a rebuild.
- **Exponential backoff**: Failed connections retry at 1s → 2s → 4s → ... → 30s max.
- **Auto token injection**: Every outgoing payload is stamped with the current `auth_token` before being sent.

#### Layer 4: React Panel (`panel/App.jsx`)
- Communicates with content scripts via **CustomEvents** (`lc-ast-update`, `lc-ws-message`, `lc-slug-change`) — clean layer separation.
- Detects LeetCode problem navigation via `window.location.pathname` regex matching and resets all state automatically.
- Implements **sequential hint unlocking**: Level 2 is only unlocked after Level 1 is used, forcing progressive learning.

#### Layer 5: Options Page (`options/Options.jsx`)
Persists `backendUrl` and `authToken` in `chrome.storage.local`, allowing any user to connect the extension to their own AWS EC2 backend without recompiling.

---

### 3.2 Backend (FastAPI + Python)

#### Application Lifecycle (`main.py`)
FastAPI's `lifespan` manager orchestrates startup and shutdown:
1. Init Redis (real or in-memory fallback)
2. Init PostgreSQL (create tables via SQLAlchemy async)
3. Seed database (idempotent insert of 54 problems)
4. Init Qdrant + warm up FastEmbed model

#### Request Pipeline (`websocket/router.py`)

| Step | Action | Failure Mode |
|------|--------|--------------|
| 1 | JSON parse + Pydantic validation | `ERROR` message |
| 1.5 | Auth token verification | `ERROR: Unauthorized` |
| 2 | Redis sliding window rate limit | `RATE_LIMIT` message |
| 3 | SHA-256 hash of code + AST + slug + action | — |
| 4 | Redis cache lookup | Skip to DONE on HIT |
| 5 | PostgreSQL problem context fetch | Proceed without context |
| 6 | LangGraph agent token streaming | `ERROR` on failure |
| 7 | Cache in Redis + upsert into Qdrant | Silent skip (non-fatal) |
| 8 | Send `DONE` | — |

#### Caching Strategy
The SHA-256 hash key is computed from:
```
hash(problem_slug + action + hint_level + selected_tier + ast_summary.json + code_text)
```
Including `code_text` is critical — it ensures any logical code change bypasses the cache and triggers a fresh LLM call, fixing the original "stale response" bug.

---

### 3.3 LangGraph AI Agent (`llm/agent.py`)

**State:**
```python
class AgentState(TypedDict):
    request: CoachRequest       # User request + AST
    context: dict               # Problem metadata from PostgreSQL
    similar_hints: list[dict]   # Retrieved from Qdrant (RAG)
    final_message: str          # LLM output
```

**Graph topology:**
```
START → retrieve_context → [conditional_edge] → generate_hint → END
                                              → evaluate_upgrade → END
```

**Node 1 — `retrieve_context_node` (RAG):**
Embeds the user's code + AST with `fastembed` (BAAI/bge-small-en-v1.5) and performs a cosine-similarity vector search in Qdrant, filtered by `problem_slug`. Returns top-2 semantically similar past hints to ground the LLM.

**Node 2 — `generate_hint_node`:**
Constructs a rich prompt combining:
- `HINT_SYSTEM_PROMPT` (Socratic persona, strict no-code-solution rules)
- Problem title, tier, and target complexity from PostgreSQL
- User's AST summary + raw code
- Retrieved similar hints (few-shot RAG context)
- Requested hint level (1=gentle, 2=deeper, 3=strong)

**Node 3 — `evaluate_upgrade_node`:**
Uses `UPGRADE_SYSTEM_PROMPT` to compare the user's code against the selected tier's target complexity. Delivers a factual, AST-grounded evaluation without revealing the solution.

**LLM Provider Factory:**

| `LLM_PROVIDER` | Model | Provider |
|---|---|---|
| `google` | `gemini-3.6-flash` | Google Generative AI |
| `anthropic` | `claude-3-5-sonnet-latest` | Anthropic |
| `openai` | `gpt-4o` | OpenAI |
| `stub` | `FakeListChatModel` | LangChain (testing) |

**Token Streaming:** Uses `astream_events(version="v1")` to intercept `on_chat_model_stream` events inside the graph. Custom extraction normalizes Gemini (list-of-dicts) and OpenAI (plain strings) chunk formats before yielding tokens.

---

### 3.4 Vector Database — RAG Layer (`vector/qdrant_store.py`)

| Property | Value |
|---|---|
| Engine | Qdrant |
| Collection | `coach_hints` |
| Embedding Model | `BAAI/bge-small-en-v1.5` via `fastembed` |
| Vector Dimension | 384 |
| Distance Metric | Cosine Similarity |
| Point ID | SHA-256 hash (first 15 hex chars → int64) |
| Payload | `{problem_slug, tier, hint_level, text[:500]}` |

Every generated hint is upserted into Qdrant post-generation. Over time, the system builds a **self-growing knowledge base** of high-quality Socratic hints that continuously improve RAG retrieval quality.

---

### 3.5 Relational Database — Knowledge Base (`db/`)

**Schema:**
```
problems
├── id (PK)
├── slug (UNIQUE INDEX)
├── title
├── difficulty (Easy / Medium / Hard)
└── category (Array, DP, Graph, Sliding Window ...)

complexity_targets
├── id (PK)
├── problem_id (FK → problems)
├── tier (BRUTE_FORCE | BETTER | OPTIMAL)
├── time_complexity  (e.g., "O(N²)")
├── space_complexity (e.g., "O(1)")
├── approach_name    (e.g., "Hash Map")
└── description
```

54 problems are seeded at startup (idempotent), each with 3 tiers of complexity targets. This structured knowledge grounds the LLM's hints in factual Big-O truth rather than hallucinated estimates.

---

## 4. WebSocket Message Protocol

**Client → Server:**
```json
{
  "problem_slug": "two-sum",
  "action": "HINT",
  "hint_level": 2,
  "selected_tier": "OPTIMAL",
  "auth_token": "my-secret-token",
  "code_text": "def twoSum(self, nums, target): ...",
  "ast_summary": {
    "nodeCount": 143, "loopDepth": 2, "hasNestedLoops": true
  }
}
```

**Server → Client (streaming):**
```json
{"type": "PROBLEM_CTX", "title": "Two Sum", "difficulty": "Easy", "tier_info": {...}}
{"type": "TOKEN", "token": "I notice "}
{"type": "TOKEN", "token": "your nested loops..."}
{"type": "DONE"}
```

**Additional message types:** `CACHE_HIT`, `RATE_LIMIT`, `ERROR`

---

## 5. Full Technology Stack

### Frontend
| Category | Technology | Role |
|---|---|---|
| Build System | Vite + `@crxjs/vite-plugin` | Chrome Extension bundling |
| UI | React 18 | Component-based floating panel |
| Styling | Tailwind CSS (`lc-` prefix) | Scoped styling in Shadow DOM |
| Code Parsing | `web-tree-sitter` (WebAssembly) | In-browser AST analysis |
| Markdown | `react-markdown` | Render LLM streaming output |
| Transport | Native WebSocket API | Real-time token streaming |
| Config | `chrome.storage.local` | Persist backend URL + auth token |

### Backend
| Category | Technology | Role |
|---|---|---|
| Framework | FastAPI | Async WS + REST server |
| Runtime | Python 3.11 + Uvicorn | ASGI async runtime |
| AI Orchestration | LangGraph + LangChain | Stateful agent graph |
| LLM | Google Gemini / Claude / GPT-4o | Generative AI |
| Embeddings | `fastembed` (BAAI/bge-small) | Local semantic embeddings |
| Vector DB | Qdrant | Hint similarity search |
| ORM | SQLAlchemy 2.0 (async) | Database access |
| Relational DB | PostgreSQL (prod) / SQLite (dev) | Problem knowledge base |
| Cache / Rate Limit | Redis (prod) / MemoryStore (dev) | Caching + rate limiting |
| Validation | Pydantic v2 | Schema enforcement |
| Config | pydantic-settings | Env-driven configuration |

### Infrastructure
| Category | Technology | Role |
|---|---|---|
| Containers | Docker + Docker Compose | Multi-service orchestration |
| Cloud | AWS EC2 | Production hosting |
| Base Images | `python:3.11-slim`, `postgres:15-alpine`, `redis:7-alpine`, `qdrant/qdrant:latest` | Service containers |
| Security | Pre-shared `SERVER_AUTH_TOKEN` | Endpoint protection |

---

## 6. Security Design

| Threat | Mitigation |
|---|---|
| Unauthorized API use | `SERVER_AUTH_TOKEN` verified on every WS message |
| API key leakage | `.env` in `.gitignore`; GitHub push protection active |
| API abuse / DoS | Redis sliding window rate limiter (10 req/60s per connection) |
| LLM cost runaway | Aggressive semantic cache (Redis TTL 1hr) avoids redundant calls |
| CSS/JS isolation | Shadow DOM prevents LeetCode page interference |

---

## 7. Data Flow — Full Request Lifecycle

```
1.  User writes Python code in Monaco editor
          ↓
2.  MutationObserver fires (600ms debounce)
          ↓
3.  ASTParser extracts code via Monaco API
    → Parses with tree-sitter WASM
    → Computes: nodeCount=143, loopDepth=2
          ↓
4.  CustomEvent → React Panel footer updates:
    "AST: 143 nodes · python"
          ↓
5.  User clicks "Hint Level 2"
          ↓
6.  wsClient reads config from chrome.storage.local
    → Assembles CoachRequest JSON + auth_token
    → Sends over WebSocket
          ↓
7.  FastAPI router.py receives message
    → Validates → Auth check → Rate limit check
    → SHA-256 hash → Redis MISS
    → Fetches context from PostgreSQL
    → Sends PROBLEM_CTX frame
          ↓
8.  LangGraph agent starts
    → retrieve_context: embeds code, searches Qdrant
    → generate_hint: builds full Socratic prompt
          ↓
9.  Gemini Flash streams tokens
    → astream_events captures each chunk
    → WebSocket sends {"type":"TOKEN","token":"..."} frames
          ↓
10. React Panel appends each token to state
    → ResponseDisplay re-renders, auto-scrolls
          ↓
11. DONE message → spinner stops
    → Full hint cached in Redis (TTL 1hr)
    → Full hint upserted into Qdrant
```

---

## 8. Deployment Architecture (AWS EC2)

```
AWS EC2 Instance
├── docker-compose up -d
│   ├── backend  :8000  (FastAPI, Python 3.11)
│   ├── postgres :5432  (PostgreSQL 15, volume: postgres_data)
│   ├── redis    :6379  (Redis 7)
│   └── qdrant   :6333  (Qdrant, volume: qdrant_data)
│
└── Environment Variables (.env or EC2 SSM)
    ├── GOOGLE_API_KEY=...
    ├── SERVER_AUTH_TOKEN=...
    ├── DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/leetcode_coach
    ├── REDIS_URL=redis://redis:6379/0
    └── QDRANT_URL=http://qdrant:6333
```

---

## 9. Key Design Decisions & Trade-offs

| Decision | Why | Trade-off |
|---|---|---|
| WebSocket over HTTP REST | Real-time token streaming; persistent connection | Connection management complexity |
| LangGraph over raw LangChain | Clean node separation; extensible agent design | Slight overhead vs. a simple chain |
| fastembed (local) over OpenAI embeddings | Zero latency, zero cost, no external API call | Slightly lower quality than `ada-002` |
| SHA-256 code hash with `code_text` | Deterministic cache key; prevents stale responses | Cache must be rebuilt if prompt templates change |
| Shadow DOM for Extension UI | Complete style isolation from LeetCode's CSS | Limits access to LeetCode's native themes |
| SQLite (dev) → PostgreSQL (prod) | Zero-config local dev; production-grade ACID | Requires driver swap via `DATABASE_URL` env var |
| Auth token in message body | Chrome WS API doesn't support custom headers | Slightly less standard than bearer tokens (OK with WSS/TLS in prod) |

---

*Document generated from full source tree analysis. Last updated: 2026-09-04.*
