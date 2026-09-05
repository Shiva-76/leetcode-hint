# DocuGraph AI — Project Status Audit

## Summary
The project is approximately **65% complete**. Phases 1, 3, and 5 have significant code, but Phase 2 is blocked by a network issue, Phase 3 has never been run end-to-end, and Phase 5 (Frontend) needs critical fixes before it can function.

---

## Phase-by-Phase Breakdown

### ✅ Phase 1: ColPali Ingestion & Qdrant — COMPLETE
All code is written, tested, and verified. The model successfully encoded a PDF page into multi-vector embeddings and upserted them into the local Qdrant database.

---

### ❌ Phase 2: Graph Extraction via Gemini & Neo4j — BLOCKED
All code is written (`neo4j_client.py`, `gemini_extraction.py`, `phase2_run.py`). It cannot run because:
1. **Network firewall** blocks outbound port 7687 (Neo4j Bolt protocol).
2. **Fix:** Install Neo4j Desktop locally (bypasses the internet entirely).

**Next action:** Install Neo4j Desktop → Start a database → Run `phase2_run.py`.

---

### ⚠️ Phase 3: FastAPI Gateway & Hybrid Retrieval — CODE EXISTS, UNTESTED
Files exist: `api/main.py`, `api/routes/retrieval.py`, `neo4j_retriever.py`, `colpali_retriever.py`. This has never been started or run.

**Issues to fix:**
- `fastapi` and `uvicorn` are not yet installed in `.venv`.
- The retrieval route needs to be verified for correctness end-to-end.
- A `requirements.txt` file should be created.

---

### ⚠️ Phase 4: Gemini 1.5 Pro Synthesis — CODE EXISTS, UNTESTED
`gemini_synthesizer.py` is written. It uses the streaming `generate_content_stream` API. However:
- It references `gemini-3.6-flash` which is **not a valid model name**. It should be `gemini-1.5-flash`.
- It is not wired up to Phase 3 retrieval yet.

---

### ⚠️ Phase 5: Next.js Frontend — SCAFFOLDED, NEEDS FIXES
A Next.js app is bootstrapped with all 3 key components (`ChatPanel.tsx`, `DocumentViewer.tsx`, `GraphViewer.tsx`). The UI looks well-designed. However:
- `react-force-graph-2d` and `framer-motion` are likely missing from `package.json`.
- The `ChatPanel` calls `/api/query` on the FastAPI backend but the endpoint URL logic needs verification.
- The app has **never been started** (`npm run dev` has never been run).

---

## Action Plan (in order)

| Priority | Task | Effort |
|---|---|---|
| 1 | **Fix Phase 2**: Install Neo4j Desktop, run `phase2_run.py` | Medium |
| 2 | **Fix Phase 4**: Correct model name `gemini-1.5-flash` in synthesizer | Tiny |
| 3 | **Fix Phase 3**: Install `fastapi`, `uvicorn`, verify API routes, start server | Small |
| 4 | **Fix Phase 5**: Install missing npm packages, fix API URL, run `npm run dev` | Small |

> [!IMPORTANT]
> Phase 2 is the only blocker that requires an external action from you (installing Neo4j Desktop). Everything else can be fixed right now with code changes.
