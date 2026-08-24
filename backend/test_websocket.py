"""
test_websocket.py — E2E WebSocket test for Phase 2.
Run: python test_websocket.py
"""
import asyncio, json, sys, urllib.request
import websockets

WS_URL   = "ws://localhost:8000/ws/coach"
HTTP_URL = "http://localhost:8000/health"

HINT_PAYLOAD = {
    "problem_slug": "two-sum", "action": "HINT", "hint_level": 1,
    "selected_tier": "OPTIMAL",
    "ast_summary": {"nodeCount": 47, "loopDepth": 2, "hasNestedLoops": True},
    "code_text": "def twoSum(self, nums, target): pass",
    "auth_token": "my-secret-token"
}
UPGRADE_PAYLOAD = {
    "problem_slug": "two-sum", "action": "UPGRADE", "hint_level": None,
    "selected_tier": "BRUTE_FORCE",
    "ast_summary": {"nodeCount": 47, "loopDepth": 2, "hasNestedLoops": True},
    "code_text": "def twoSum(self, nums, target): pass",
    "auth_token": "my-secret-token"
}
INVALID_PAYLOAD = {"totally": "wrong"}

results = []

def check(label, ok, detail=""):
    mark = "PASS" if ok else "FAIL"
    print(f"  [{mark}] {label}" + (f"  ({detail})" if detail else ""))
    results.append(ok)
    return ok

async def collect(payload, max_msgs=300):
    msgs = []
    try:
        async with websockets.connect(WS_URL) as ws:
            await ws.send(json.dumps(payload))
            for _ in range(max_msgs):
                raw = await asyncio.wait_for(ws.recv(), timeout=60)
                msg = json.loads(raw)
                msgs.append(msg)
                if msg.get("type") in ("DONE", "ERROR", "RATE_LIMIT"):
                    break
    except Exception as e:
        msgs.append({"type": "EXCEPTION", "message": str(e)})
    return msgs

def test_health():
    print("\n[1] Health Check")
    try:
        data = json.loads(urllib.request.urlopen(HTTP_URL, timeout=5).read())
        check("status == ok",     data.get("status") == "ok")
        check("redis field",      "redis" in data, data.get("redis"))
        check("llm_provider",     "llm_provider" in data, data.get("llm_provider"))
        return True
    except Exception as e:
        check("server reachable", False, str(e)); return False

async def test_hint():
    print("\n[2] HINT L1 — Token streaming")
    msgs = await collect(HINT_PAYLOAD)
    types = [m["type"] for m in msgs]
    tokens = [m for m in msgs if m["type"] == "TOKEN"]
    text = "".join(m["token"] for m in tokens)
    check("got TOKEN messages",  len(tokens) > 0,     f"{len(tokens)} tokens")
    check("ends with DONE",      types[-1] == "DONE")
    check("no ERROR in stream",  "ERROR" not in types)
    check("text len > 20 chars", len(text) > 20,      f"{len(text)} chars")
    print(f"     Preview: {text[:100]}...")

async def test_cache():
    print("\n[3] Cache Hit — same request again")
    msgs = await collect(HINT_PAYLOAD)
    types = [m["type"] for m in msgs]
    check("CACHE_HIT received",  "CACHE_HIT" in types)
    check("tokens still stream", "TOKEN" in types)
    check("ends with DONE",      types[-1] == "DONE")

async def test_upgrade():
    print("\n[4] UPGRADE action")
    msgs = await collect(UPGRADE_PAYLOAD)
    types = [m["type"] for m in msgs]
    tokens = [m for m in msgs if m["type"] == "TOKEN"]
    check("got TOKEN messages",  len(tokens) > 0)
    check("ends with DONE",      types[-1] == "DONE")

async def test_invalid():
    print("\n[5] Invalid payload -> ERROR (no crash)")
    msgs = await collect(INVALID_PAYLOAD)
    types = [m["type"] for m in msgs]
    check("ERROR returned",      "ERROR" in types)

async def test_unauthorized():
    print("\n[6] Unauthorized -> ERROR")
    bad_payload = {**HINT_PAYLOAD, "auth_token": "wrong"}
    msgs = await collect(bad_payload)
    types = [m["type"] for m in msgs]
    check("ERROR returned", "ERROR" in types)
    if "ERROR" in types:
        msg = next(m for m in msgs if m["type"] == "ERROR")
        check("Unauthorized message", "Unauthorized" in msg.get("message", ""))

async def main():
    print("=" * 52)
    print("  Phase 2 E2E WebSocket Test")
    print("=" * 52)
    if not test_health():
        print("Server not reachable — aborting."); sys.exit(1)
    await test_hint()
    await test_cache()
    await test_upgrade()
    await test_invalid()
    await test_unauthorized()
    passed = sum(results); total = len(results)
    print(f"\n{'='*52}")
    print(f"  {passed}/{total} checks passed" + (" -- ALL GOOD!" if passed == total else " -- SOME FAILED"))
    print("=" * 52)
    sys.exit(0 if passed == total else 1)

asyncio.run(main())
