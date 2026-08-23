# Phase 4: LangGraph AI Agent Implementation Plan

This phase replaces our simulated `stub_streamer` with a fully functional LangGraph pipeline powered by real LLMs (Claude 3.5 Sonnet / GPT-4o) and semantic vector search.

## User Review Required

> [!IMPORTANT]
> **Embedding Model Selection:** In Phase 3, we used a SHA-256 hash as a placeholder for our vector embeddings. For Phase 4, we need real semantic embeddings to find similar coding patterns in Qdrant. 
> 
> **Decision needed:** I recommend using `fastembed`. It's a lightweight, extremely fast local embedding library that doesn't require massive GPU frameworks like PyTorch, keeping your development environment clean. Is this acceptable, or do you prefer using an external API for embeddings (like OpenAI `text-embedding-3-small`)?

> [!WARNING]
> **API Keys:** To test the real AI, you will need to put either a valid `ANTHROPIC_API_KEY` or `OPENAI_API_KEY` in the `backend/.env` file. We will configure the graph to automatically pick up whichever one you provide.

## Proposed Changes

We will build the graph in a new `backend/app/llm/agent.py` file and wire it into the existing WebSocket router.

---

### Backend: Agent Configuration

#### [NEW] `backend/app/llm/agent.py`
This will contain the core LangGraph state machine.
- **State**: `AgentState` containing the `CoachRequest`, DB `context`, retrieved `similar_hints`, and final `response`.
- **Nodes**: 
  1. `retrieve_context`: Embeds the user's current code and AST summary, querying Qdrant for similar past hints to avoid repeating bad advice or to draw on past successful coaching strategies.
  2. `generate_hint`: For `action="HINT"`. Uses a highly tuned system prompt that instructs the LLM to act as a Socratic coach, reading the AST `loop_depth` and `has_nested_loops` to guide the user towards the `target_complexity` from the DB without giving away the answer.
  3. `evaluate_upgrade`: For `action="UPGRADE"`. Evaluates the user's current code against the next tier's complexity targets.
- **Compilation**: The graph will be compiled and expose an `astream_events` generator.

#### [NEW] `backend/app/llm/prompts.py`
- Cleanly separate our System Prompts from the logic. We will define strict Socratic rules here.

### Backend: Integrations

#### [MODIFY] `backend/app/vector/qdrant_store.py`
- Replace the deterministic `_embed(text)` SHA-256 stub with `fastembed` (or chosen embedder). 
- Update `store_hint` and `search_similar_hints` to use real semantic text (combining the AST structure and code snippet).

#### [MODIFY] `backend/app/websocket/router.py`
- Replace `from app.llm.stub_streamer import stream_stub_response` with our new LangGraph runner.
- Parse the async stream from `astream_events` to yield tokens exactly as the extension expects (`{ "type": "TOKEN", "token": "..." }`).

#### [MODIFY] `backend/requirements.txt`
- Add `langgraph`, `langchain-core`, `langchain-anthropic`, `langchain-openai`, and `fastembed`.

## Verification Plan

### Automated Tests
- Re-run `test_websocket.py`. We will swap `LLM_PROVIDER=stub` to `LLM_PROVIDER=openai` (or `anthropic`) in the test environment to ensure the graph streams valid JSON tokens and successfully parses real LLM responses without crashing.

### Manual Verification
- Start the server and extension.
- Ask for a Hint L1 on a problem. Verify the AI streams a response acknowledging the target time complexity.
- Ask for a Hint L2 and verify it builds upon L1.
- Write a brute-force `O(N^2)` solution, ask for an upgrade to `O(N)`, and verify the AI accurately critiques the nested loops using the AST data.
