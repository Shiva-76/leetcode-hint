"""
schemas.py — Pydantic models for WebSocket message validation.
"""
from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ── Incoming payload (Client → Server) ───────────────────────────────────────

class ASTSummary(BaseModel):
    language: str = "unknown"
    node_count: int = Field(0, alias="nodeCount")
    loop_depth: int = Field(0, alias="loopDepth")
    has_nested_loops: bool = Field(False, alias="hasNestedLoops")
    loops: list[dict[str, Any]] = []
    functions: list[dict[str, Any]] = []

    model_config = {"populate_by_name": True}


class CoachRequest(BaseModel):
    problem_slug: str
    action: Literal["HINT", "UPGRADE"]
    hint_level: Optional[Literal[1, 2, 3]] = None
    selected_tier: Optional[Literal["BRUTE_FORCE", "BETTER", "OPTIMAL"]] = None
    ast_summary: Optional[ASTSummary] = None
    code_text: str = ""
    auth_token: str = ""


# ── Outgoing messages (Server → Client) ──────────────────────────────────────

class TokenMessage(BaseModel):
    type: Literal["TOKEN"] = "TOKEN"
    token: str


class DoneMessage(BaseModel):
    type: Literal["DONE"] = "DONE"


class CacheHitMessage(BaseModel):
    type: Literal["CACHE_HIT"] = "CACHE_HIT"
    cached: bool = True


class ErrorMessage(BaseModel):
    type: Literal["ERROR"] = "ERROR"
    message: str


class RateLimitMessage(BaseModel):
    type: Literal["RATE_LIMIT"] = "RATE_LIMIT"
    message: str = "Rate limit exceeded. Please wait before sending another request."
    retry_after: int = 60


# ── Feedback (Client → Server via REST) ──────────────────────────────────────

class FeedbackRequest(BaseModel):
    hint_id: str                        # SHA-256 req_hash returned in DONE message
    vote: Literal["up", "down"]         # "up" = keep, "down" = delete from Qdrant
