"""Priority-0 web-bridge security: deny-by-default auth and per-client rate limiting.

Hermetic and offline. All state is driven through env (monkeypatched) and FastAPI's in-process
TestClient -- no real sockets or network beyond TestClient. Skips cleanly where FastAPI/httpx are
absent, matching how tests/test_mcp.py guards optional deps.
"""
import os
import sys

import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")
from fastapi.testclient import TestClient  # noqa: E402  (import after the skip guards)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "web", "server"))

KEY = "unit-test-key-123"
AUTH = {"X-API-Key": KEY}


def _client(monkeypatch, *, api_key=KEY, rate_per_min=None):
    """Build a TestClient with env configured, then reset the shared rate-limiter bucket.

    Passing api_key=None leaves CAMBIUM_API_KEY unset (the locked-server case).
    """
    import app
    if api_key is None:
        monkeypatch.delenv("CAMBIUM_API_KEY", raising=False)
    else:
        monkeypatch.setenv("CAMBIUM_API_KEY", api_key)
    if rate_per_min is None:
        monkeypatch.delenv("CAMBIUM_RATE_PER_MIN", raising=False)
    else:
        monkeypatch.setenv("CAMBIUM_RATE_PER_MIN", str(rate_per_min))
    app.security.limiter.reset()
    return TestClient(app.app), app


# (c) /health (and /api/health) are reachable without a key.
def test_health_is_unauthenticated(monkeypatch):
    c, _ = _client(monkeypatch)
    assert c.get("/health").status_code == 200
    assert c.get("/health").json() == {"status": "ok"}
    assert c.get("/api/health").status_code == 200          # documented health endpoint stays open too


# (a-part-1) a protected endpoint returns 401 without a key when CAMBIUM_API_KEY is set.
def test_protected_endpoint_401_without_key(monkeypatch):
    c, _ = _client(monkeypatch)
    r = c.post("/api/run", json={"task": "verify these results"})
    assert r.status_code == 401
    assert "key" in r.json()["detail"].lower()


def test_protected_endpoint_401_with_wrong_key(monkeypatch):
    c, _ = _client(monkeypatch)
    r = c.post("/api/run", json={"task": "verify these results"}, headers={"X-API-Key": "not-the-key"})
    assert r.status_code == 401


# (a-part-2) the right key succeeds (200) when CAMBIUM_API_KEY is set.
def test_protected_endpoint_200_with_right_key(monkeypatch):
    c, _ = _client(monkeypatch)
    r = c.post("/api/run", json={"task": "verify these results"}, headers=AUTH)
    assert r.status_code == 200
    body = r.json()
    assert "run_id" in body and body["plan"]["kind"]


def test_bearer_token_also_accepted(monkeypatch):
    c, _ = _client(monkeypatch)
    r = c.post("/api/run", json={"task": "verify these results"},
               headers={"Authorization": "Bearer " + KEY})
    assert r.status_code == 200


def test_gate_endpoint_is_protected(monkeypatch):
    c, _ = _client(monkeypatch)
    assert c.post("/api/gate/whatever/decide", json={"decision": "APPROVE"}).status_code == 401
    # With the key, auth passes and the handler's own validation runs (unknown run -> 404).
    assert c.post("/api/gate/whatever/decide", json={"decision": "APPROVE"}, headers=AUTH).status_code == 404


# (b) with CAMBIUM_API_KEY unset the protected endpoint returns 503 (locked, not open).
def test_protected_endpoint_503_when_key_unset(monkeypatch):
    c, _ = _client(monkeypatch, api_key=None)
    r = c.post("/api/run", json={"task": "verify these results"})
    assert r.status_code == 503
    assert "CAMBIUM_API_KEY" in r.json()["detail"]
    # Even a caller who guesses a key cannot get in while the server is unconfigured.
    assert c.post("/api/run", json={"task": "x"}, headers={"X-API-Key": "guess"}).status_code == 503


# (d) exceeding the rate limit returns 429 (limit dialed low via env for the test).
def test_rate_limit_returns_429(monkeypatch):
    c, _ = _client(monkeypatch, rate_per_min=3)
    codes = [c.post("/api/run", json={"task": "x"}, headers=AUTH).status_code for _ in range(6)]
    assert codes[:3] == [200, 200, 200]     # first three within budget
    assert 429 in codes[3:]                 # subsequent calls exceed the per-minute cap
    over = c.post("/api/run", json={"task": "x"}, headers=AUTH)
    assert over.status_code == 429
    assert "rate limit" in over.json()["detail"].lower()


def test_auth_is_checked_before_rate_limit(monkeypatch):
    # An unauthenticated flood must not be able to exhaust a client's token budget: 401 comes first.
    c, _ = _client(monkeypatch, rate_per_min=2)
    codes = [c.post("/api/run", json={"task": "x"}).status_code for _ in range(5)]
    assert set(codes) == {401}              # never 429 -> auth short-circuits before the bucket


# WebSocket event stream is also gated: no key -> closed with an error frame, right key -> connects.
def test_websocket_stream_requires_key(monkeypatch):
    c, _ = _client(monkeypatch)
    with c.websocket_connect("/api/stream/does-not-exist") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "error" and "key" in msg["message"].lower()


def test_websocket_stream_accepts_key_query_param(monkeypatch):
    c, app = _client(monkeypatch)
    # Create a real run so the stream has something to attach to, then connect with ?key=.
    run_id = c.post("/api/run", json={"task": "verify these results"}, headers=AUTH).json()["run_id"]
    with c.websocket_connect("/api/stream/%s?key=%s" % (run_id, KEY)) as ws:
        first = ws.receive_json()
        assert first["type"] != "error"     # authenticated: real run events, not an auth rejection
