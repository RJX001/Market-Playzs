"""In-memory rate limiting for MVP.

TODO: Replace with Redis (or Upstash) before multi-instance / production scale.
Vercel Fluid Compute can run multiple instances — in-memory counters will not
be shared across them.
"""

from __future__ import annotations

import time
from collections import defaultdict
from threading import Lock

from fastapi import HTTPException, Request, status

# Login: 5 attempts per IP per 15 minutes (Section 5.1)
LOGIN_MAX_ATTEMPTS = 5
LOGIN_WINDOW_SECONDS = 15 * 60

# Global: 100 requests per minute per authenticated user (Section 5.1)
USER_MAX_REQUESTS = 100
USER_WINDOW_SECONDS = 60

_lock = Lock()
_login_attempts: dict[str, list[float]] = defaultdict(list)
_user_requests: dict[str, list[float]] = defaultdict(list)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


def _prune(timestamps: list[float], *, now: float, window: float) -> list[float]:
    cutoff = now - window
    return [ts for ts in timestamps if ts >= cutoff]


def check_login_rate_limit(request: Request) -> None:
    """Raise 429 if this IP exceeded login attempts in the window."""
    ip = _client_ip(request)
    now = time.monotonic()
    with _lock:
        recent = _prune(_login_attempts[ip], now=now, window=LOGIN_WINDOW_SECONDS)
        _login_attempts[ip] = recent
        if len(recent) >= LOGIN_MAX_ATTEMPTS:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many login attempts. Try again in 15 minutes.",
            )


def record_login_attempt(request: Request) -> None:
    """Record a login attempt (success or failure) against the client IP."""
    ip = _client_ip(request)
    now = time.monotonic()
    with _lock:
        recent = _prune(_login_attempts[ip], now=now, window=LOGIN_WINDOW_SECONDS)
        recent.append(now)
        _login_attempts[ip] = recent


def check_user_rate_limit(user_id: str) -> None:
    """Raise 429 if authenticated user exceeded 100 req/min."""
    now = time.monotonic()
    with _lock:
        recent = _prune(_user_requests[user_id], now=now, window=USER_WINDOW_SECONDS)
        if len(recent) >= USER_MAX_REQUESTS:
            _user_requests[user_id] = recent
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Max 100 requests per minute.",
            )
        recent.append(now)
        _user_requests[user_id] = recent


def reset_rate_limits_for_tests() -> None:
    """Clear in-memory stores — tests only."""
    with _lock:
        _login_attempts.clear()
        _user_requests.clear()
