"""
hashing.py — Deterministic SHA-256 hash of a CoachRequest.

The hash captures the minimum set of fields that fully define a unique
coaching request:
  - problem_slug   (WHICH problem)
  - action         (HINT vs UPGRADE)
  - hint_level     (which of L1/L2/L3)
  - selected_tier  (BRUTE_FORCE / BETTER / OPTIMAL)
  - code_text      (the actual code — stripped of leading/trailing whitespace)

Note: loop_depth and node_count are intentionally excluded because they are
derived FROM the raw code. Including them alongside code_text is redundant —
the same code always produces the same AST metrics.
"""
import hashlib
import json

from app.schemas import CoachRequest


def compute_request_hash(req: CoachRequest) -> str:
    """
    Returns a hex SHA-256 string that uniquely identifies a coaching request.
    """
    key_data = {
        "slug":       req.problem_slug,
        "action":     req.action,
        "hint_level": req.hint_level,
        "tier":       req.selected_tier,
        "code":       req.code_text.strip() if req.code_text else "",
    }
    raw = json.dumps(key_data, sort_keys=True)
    return hashlib.sha256(raw.encode()).hexdigest()
