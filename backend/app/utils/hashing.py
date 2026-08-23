"""
hashing.py — Deterministic SHA-256 hash of a CoachRequest.

The hash captures:
  - problem_slug   (WHICH problem)
  - action         (HINT vs UPGRADE)
  - hint_level     (which of L1/L2/L3)
  - selected_tier  (BRUTE_FORCE / BETTER / OPTIMAL)
  - ast.loop_depth (structural complexity class of the code)
  - ast.node_count (rough size of the code)

We intentionally EXCLUDE raw code text so that cosmetically different
code that has the same structure (renamed vars, extra blank lines) still
gets a cache hit.
"""
import hashlib
import json

from app.schemas import CoachRequest


def compute_request_hash(req: CoachRequest) -> str:
    """
    Returns a hex SHA-256 string that uniquely identifies a coaching request
    based on structural semantics (not raw code text).
    """
    key_data = {
        "slug":       req.problem_slug,
        "action":     req.action,
        "hint_level": req.hint_level,
        "tier":       req.selected_tier,
        "loop_depth": req.ast_summary.loop_depth if req.ast_summary else 0,
        "node_count": req.ast_summary.node_count if req.ast_summary else 0,
    }
    raw = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()
