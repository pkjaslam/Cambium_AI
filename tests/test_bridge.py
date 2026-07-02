"""Cambium bridge: routing, the gate pause/resume loop, and the REST endpoints.

The bridge is optional (web/); these tests skip cleanly if FastAPI isn't installed (e.g. core CI)."""
import asyncio, os, sys
import pytest
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "web", "server"))

# ---- engine: routing reuses the real task_router ----
def test_plan_routes_by_request_type():
    import engine
    assert engine.plan_for("write an NSF proposal")["kind"] == "grant"
    assert engine.plan_for("write the quarterly progress report")["kind"] == "report"
    p = engine.plan_for("write an NSF proposal on wildfire")
    assert "Orchestration" in p["active"] and any(ph["gate"] for ph in p["phases"])

# ---- engine: the gate PAUSES the run until a human decides, then resumes ----
def test_gate_pauses_then_resumes():
    import engine
    async def scenario():
        r = engine.Run("write the quarterly progress report")
        task = asyncio.create_task(r.drive(step=0))
        seen, decided = [], False
        while True:
            ev = await asyncio.wait_for(r.queue.get(), timeout=5)
            if ev is None: break
            seen.append(ev["type"])
            if ev["type"] == "gate.open":
                # the run is now blocked waiting; the human approves each gate it
                # reaches (robust to runs that legitimately have more than one gate) ->
                r.decide("APPROVE"); decided = True
        await task
        return seen
    seen = asyncio.run(scenario())
    assert "run.started" in seen and "gate.open" in seen
    assert seen.index("gate.decided") > seen.index("gate.open")
    assert seen[-1] == "run.done"

def test_reject_stops_the_run():
    import engine
    async def scenario():
        r = engine.Run("write the quarterly progress report")
        task = asyncio.create_task(r.drive(step=0)); types = []
        while True:
            ev = await asyncio.wait_for(r.queue.get(), timeout=5)
            if ev is None: break
            types.append(ev["type"])
            if ev["type"] == "gate.open": r.decide("REJECT")
        await task
        return r, types
    r, types = asyncio.run(scenario())
    assert r.summary()["gates"][-1]["decision"] == "REJECT"

# ---- REST endpoints (no WS interleave -> no TestClient deadlock) ----
# The bridge now enforces deny-by-default API-key auth (see web/server/security.py and
# tests/test_web_security.py for the auth/rate-limit behavior). These endpoint tests target the
# request-validation logic, so they configure a key and send it; the auth contract itself is
# covered separately.
_TEST_KEY = "bridge-test-key"
_AUTH = {"X-API-Key": _TEST_KEY}

def _client(monkeypatch):
    pytest.importorskip("fastapi"); pytest.importorskip("httpx")
    monkeypatch.setenv("CAMBIUM_API_KEY", _TEST_KEY)
    from fastapi.testclient import TestClient
    import app
    app.security.limiter.reset()
    return TestClient(app.app)

def test_health_and_run_and_validation(monkeypatch):
    c = _client(monkeypatch)
    h = c.get("/api/health").json()                      # health stays unauthenticated
    assert h["ok"] and h["mode"] in ("simulation", "live")
    r = c.post("/api/run", json={"task": "verify these results"}, headers=_AUTH).json()
    assert "run_id" in r and r["plan"]["kind"]
    assert c.post("/api/run", json={"task": ""}, headers=_AUTH).status_code == 400
    assert c.post("/api/gate/nope/decide", json={"decision": "APPROVE"}, headers=_AUTH).status_code == 404
    assert c.post("/api/gate/%s/decide" % r["run_id"], json={"decision": "MAYBE"}, headers=_AUTH).status_code == 400
