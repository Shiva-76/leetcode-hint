"""
stub_streamer.py — Simulates LLM token streaming for Phase 2.

Returns realistic Socratic hint text based on action + hint_level.
In Phase 4, this module is replaced by the LangGraph pipeline.

Yields tokens (strings) asynchronously with realistic timing.
"""
from __future__ import annotations
import asyncio
from typing import AsyncGenerator

from app.schemas import CoachRequest

# ── Stub responses per action / hint level ────────────────────────────────────

STUB_HINTS: dict[tuple[str, int | None], str] = {
    ("HINT", 1): (
        "Your loop iterates through every pair — but do you **really** need to "
        "check *both* elements of each pair independently? "
        "What happens when `nums[i] + nums[j] == target`?"
    ),
    ("HINT", 2): (
        "Let's trace through `nums = [2, 7, 11, 15]`, `target = 9`:\n\n"
        "- Outer loop `i=0` → `nums[0] = 2`. "
        "We need its **complement**: `9 - 2 = 7`.\n"
        "- Inner loop `j=1` → `nums[1] = 7`. ✅ Found!\n\n"
        "Your approach works, but you scanned up to `j=1` before finding it. "
        "**What if you had already stored complements as you walked the array once?** "
        "Could you answer *'have I seen 7 before?'* in O(1) instead of scanning?"
    ),
    ("HINT", 3): (
        "**Your approach** uses a nested loop → O(N²) time.\n\n"
        "**The key insight**: for each `nums[i]`, you need to know if "
        "`target - nums[i]` exists elsewhere. A **hash map** answers this in O(1).\n\n"
        "```python\n"
        "def twoSum(self, nums, target):\n"
        "    seen = {}  # value → index\n"
        "    for i, num in enumerate(nums):\n"
        "        complement = target - num\n"
        "        if complement in seen:\n"
        "            return [seen[complement], i]\n"
        "        seen[num] = i\n"
        "```\n\n"
        "This is **O(N) time, O(N) space** — one pass, no nested loops."
    ),
}

STUB_UPGRADE: dict[str, str] = {
    "BRUTE_FORCE": (
        "Nice work getting a correct brute-force solution! 🎉\n\n"
        "Your current approach checks every pair — that's **O(N²)**. "
        "To move to the **Better** tier, ask yourself: "
        "*could sorting the array let you use two pointers instead of nested loops?* "
        "What data structure lets you eliminate one loop entirely?"
    ),
    "BETTER": (
        "Solid improvement! You're already past the naive approach. 🔥\n\n"
        "To reach **Optimal**, think about this: "
        "*can you solve Two Sum in a **single pass** without sorting?* "
        "Which data structure gives you O(1) lookup of a previously seen value?"
    ),
    "OPTIMAL": (
        "🏆 **Congratulations!** Your solution is already at peak efficiency.\n\n"
        "You've achieved **O(N) time, O(N) space** — the best possible for Two Sum. "
        "This is the canonical hash map pattern used in real interviews and production code. "
        "No further structural improvement is possible!"
    ),
}


async def stream_stub_response(req: CoachRequest) -> AsyncGenerator[str, None]:
    """
    Yield tokens from a stub response with realistic streaming delays.
    Simulates an LLM streaming ~4 tokens/second.
    """
    if req.action == "HINT" and req.hint_level is not None:
        text = STUB_HINTS.get(("HINT", req.hint_level), _fallback_hint(req))
    elif req.action == "UPGRADE":
        tier = req.selected_tier or "BRUTE_FORCE"
        text = STUB_UPGRADE.get(tier, STUB_UPGRADE["BRUTE_FORCE"])
    else:
        text = "Please select a strategy and try again."

    # Stream word by word with a slight delay to simulate LLM tokens
    words = text.split(" ")
    for i, word in enumerate(words):
        token = word if i == len(words) - 1 else word + " "
        yield token
        # ~40-60ms per token → natural reading speed
        await asyncio.sleep(0.05)


def _fallback_hint(req: CoachRequest) -> str:
    return (
        f"Think carefully about your approach for **{req.problem_slug}**. "
        "What is the bottleneck in your current solution? "
        "Can you eliminate redundant work?"
    )
