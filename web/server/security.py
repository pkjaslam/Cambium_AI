"""Security primitives for the Cambium bridge: deny-by-default auth and in-process rate limiting.

Two concerns, kept out of app.py so they can be unit-tested in isolation:

  1. require_key -- a FastAPI dependency. It reads the expected key from CAMBIUM_API_KEY and
     compares it (constant-time, via hmac.compare_digest) against the caller's X-API-Key header
     or Authorization: Bearer token. Deny-by-default: if CAMBIUM_API_KEY is unset the endpoint is
     LOCKED (503) rather than open, so an unconfigured deploy is closed, not wide open. A present
     env var with a wrong/missing caller key is 401.

  2. RateLimiter -- a tiny per-client token bucket keyed by client IP + presented key. Zero new
     dependencies (safer for CI than pulling in slowapi). The default rate is CAMBIUM_RATE_PER_MIN
     requests/min/client (default 60); exceeding it raises HTTPException(429).

Both read their config from the environment at call time, so tests can monkeypatch env freely.
"""
import hmac
import os
import threading
import time

from fastapi import HTTPException, Request

API_KEY_ENV = "CAMBIUM_API_KEY"
RATE_ENV = "CAMBIUM_RATE_PER_MIN"
DEFAULT_RATE_PER_MIN = 60


def _presented_key(request: Request) -> str:
    """Pull the caller's key from X-API-Key, or from an Authorization: Bearer <token> header."""
    key = request.headers.get("x-api-key")
    if key:
        return key
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    return ""


async def require_key(request: Request) -> None:
    """FastAPI dependency enforcing deny-by-default API-key auth.

    503 if CAMBIUM_API_KEY is unset (server not configured -> locked, never open).
    401 if the caller's key is missing or does not match. Returns None on success.
    """
    expected = os.environ.get(API_KEY_ENV)
    if not expected:
        raise HTTPException(status_code=503, detail="server auth not configured: set CAMBIUM_API_KEY")
    presented = _presented_key(request)
    if not presented or not hmac.compare_digest(presented, expected):
        raise HTTPException(status_code=401, detail="invalid or missing API key")


def _rate_per_min() -> int:
    """Read CAMBIUM_RATE_PER_MIN at call time; fall back to the default on unset/garbage."""
    raw = os.environ.get(RATE_ENV)
    if raw is None:
        return DEFAULT_RATE_PER_MIN
    try:
        val = int(raw)
    except (TypeError, ValueError):
        return DEFAULT_RATE_PER_MIN
    return val if val > 0 else DEFAULT_RATE_PER_MIN


class RateLimiter:
    """Thread-safe in-process token bucket, one bucket per client identity.

    Capacity and refill both track CAMBIUM_RATE_PER_MIN, read fresh on every check so tests can
    dial the limit down via monkeypatch. Identity is client IP + presented key, so two callers
    behind one IP with distinct keys do not share a bucket. This is per-process only: it is a
    sane first line of defense, not a substitute for an edge/gateway limiter in a multi-replica
    deployment (documented honestly rather than overclaimed).
    """

    def __init__(self) -> None:
        self._buckets = {}   # identity -> (tokens, last_refill_ts)
        self._lock = threading.Lock()

    @staticmethod
    def _identity(request: Request) -> str:
        client = request.client.host if request.client else "unknown"
        return client + "|" + _presented_key(request)

    def check(self, request: Request) -> None:
        """Consume one token for this client; raise HTTPException(429) when the bucket is empty."""
        rate = _rate_per_min()
        capacity = float(rate)
        refill_per_sec = rate / 60.0
        now = time.monotonic()
        ident = self._identity(request)
        with self._lock:
            tokens, last = self._buckets.get(ident, (capacity, now))
            tokens = min(capacity, tokens + (now - last) * refill_per_sec)
            if tokens < 1.0:
                self._buckets[ident] = (tokens, now)
                raise HTTPException(
                    status_code=429,
                    detail="rate limit exceeded: max %d requests/min per client" % rate,
                )
            self._buckets[ident] = (tokens - 1.0, now)

    def reset(self) -> None:
        """Drop all buckets. Test-only helper so one test's spend does not bleed into another."""
        with self._lock:
            self._buckets.clear()


# Module-level limiter shared by the app; import this instance, do not construct a second one.
limiter = RateLimiter()


async def rate_limit(request: Request) -> None:
    """FastAPI dependency wrapper around the shared limiter."""
    limiter.check(request)
