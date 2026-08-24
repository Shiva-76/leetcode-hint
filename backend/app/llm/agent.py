"""
agent.py — LangGraph AI Agent for generating Socratic hints and evaluating code upgrades.
"""
from typing import TypedDict, Any, AsyncGenerator
import json

from langchain_core.messages import SystemMessage, HumanMessage
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, START, END

from app.config import settings
from app.schemas import CoachRequest
from app.vector.qdrant_store import search_similar_hints
from app.llm.prompts import HINT_SYSTEM_PROMPT, UPGRADE_SYSTEM_PROMPT

# State Definition
class AgentState(TypedDict):
    request: CoachRequest
    context: dict[str, Any]
    similar_hints: list[dict[str, Any]]
    final_message: str


# ── LLM Initialisation ────────────────────────────────────────────────────────

def get_llm():
    if settings.llm_provider == "stub":
        from langchain_core.language_models import FakeListChatModel
        return FakeListChatModel(responses=["This is a stub Socratic hint based on your AST."])
    if settings.llm_provider == "google" and settings.google_api_key:
        return ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=settings.google_api_key)
    if settings.llm_provider == "anthropic" and settings.anthropic_api_key:
        return ChatAnthropic(model="claude-3-5-sonnet-latest", api_key=settings.anthropic_api_key)
    elif settings.llm_provider == "openai" and settings.openai_api_key:
        return ChatOpenAI(model="gpt-4o", api_key=settings.openai_api_key)
    else:
        # Fallback
        if settings.google_api_key:
             return ChatGoogleGenerativeAI(model="gemini-3.6-flash", google_api_key=settings.google_api_key)
        elif settings.openai_api_key:
             return ChatOpenAI(model="gpt-4o", api_key=settings.openai_api_key)
        elif settings.anthropic_api_key:
             return ChatAnthropic(model="claude-3-5-sonnet-latest", api_key=settings.anthropic_api_key)
        raise RuntimeError("No LLM API key provided in .env")

# ── Nodes ─────────────────────────────────────────────────────────────────────

async def retrieve_context_node(state: AgentState) -> AgentState:
    """Retrieve similar past hints from Qdrant based on the current code and AST."""
    req = state["request"]
    query_text = f"Code:\n{req.code_text}\nAST Nodes: {req.ast_summary.node_count if req.ast_summary else 0}"
    similar = search_similar_hints(query_text=query_text, problem_slug=req.problem_slug, limit=2)
    return {"similar_hints": similar}


async def generate_hint_node(state: AgentState) -> AgentState:
    """Generate a Socratic hint using the LLM."""
    req = state["request"]
    ctx = state["context"]
    llm = get_llm()

    # Format the prompt
    system_msg = HINT_SYSTEM_PROMPT.format(loop_depth=req.ast_summary.loop_depth if req.ast_summary else 0)
    
    human_content = (
        f"Problem: {ctx.get('title', req.problem_slug)}\n"
        f"Target Tier: {ctx.get('tier', 'Unknown')}\n"
        f"Target Time: {ctx.get('time_complexity', '?')}\n"
        f"Target Space: {ctx.get('space_complexity', '?')}\n"
        f"Target Approach: {ctx.get('approach_name', '')} - {ctx.get('description', '')}\n\n"
        f"User AST Summary: {json.dumps(req.ast_summary.model_dump() if req.ast_summary else {})}\n"
        f"Requested Hint Level: {req.hint_level}\n\n"
        f"User Code:\n{req.code_text}\n\n"
        f"Similar Past Hints retrieved:\n{json.dumps(state['similar_hints'])}\n"
    )

    response = await llm.ainvoke([SystemMessage(content=system_msg), HumanMessage(content=human_content)])
    return {"final_message": response.content}


async def evaluate_upgrade_node(state: AgentState) -> AgentState:
    """Evaluate if the user's code matches the next tier."""
    req = state["request"]
    ctx = state["context"]
    llm = get_llm()

    human_content = (
        f"Problem: {ctx.get('title', req.problem_slug)}\n"
        f"Target Tier: {ctx.get('tier', 'Unknown')}\n"
        f"Target Time: {ctx.get('time_complexity', '?')}\n"
        f"Target Space: {ctx.get('space_complexity', '?')}\n\n"
        f"User AST Summary: {json.dumps(req.ast_summary.model_dump() if req.ast_summary else {})}\n"
        f"User Code:\n{req.code_text}\n"
    )

    response = await llm.ainvoke([SystemMessage(content=UPGRADE_SYSTEM_PROMPT), HumanMessage(content=human_content)])
    return {"final_message": response.content}

# ── Router ────────────────────────────────────────────────────────────────────

def route_action(state: AgentState) -> str:
    """Route to HINT or UPGRADE node based on the request action."""
    action = state["request"].action
    if action == "HINT":
        return "generate_hint"
    elif action == "UPGRADE":
        return "evaluate_upgrade"
    return END

# ── Graph Compilation ─────────────────────────────────────────────────────────

builder = StateGraph(AgentState)
builder.add_node("retrieve_context", retrieve_context_node)
builder.add_node("generate_hint", generate_hint_node)
builder.add_node("evaluate_upgrade", evaluate_upgrade_node)

builder.add_edge(START, "retrieve_context")
builder.add_conditional_edges("retrieve_context", route_action, ["generate_hint", "evaluate_upgrade"])
builder.add_edge("generate_hint", END)
builder.add_edge("evaluate_upgrade", END)

agent_graph = builder.compile()

# ── Entry Point ───────────────────────────────────────────────────────────────

async def stream_agent_response(
    req: CoachRequest,
    context: dict | None = None
) -> AsyncGenerator[str, None]:
    """
    Yield tokens from the LangGraph agent execution.
    Handles the `astream_events` API from LangChain to stream the LLM output token-by-token.
    """
    initial_state = {
        "request": req,
        "context": context or {},
        "similar_hints": [],
        "final_message": ""
    }
    
    # We use astream_events to get granular token streaming from the LLM inside the graph
    async for event in agent_graph.astream_events(initial_state, version="v1"):
        kind = event["event"]
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                if isinstance(content, list):
                    for part in content:
                        if isinstance(part, dict) and "text" in part:
                            yield part["text"]
                        elif isinstance(part, str):
                            yield part
                elif isinstance(content, str):
                    yield content
