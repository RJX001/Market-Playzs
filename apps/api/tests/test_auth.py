"""Unit tests for auth service (password + JWT) and rate limits — no DB required."""

from __future__ import annotations

import uuid

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.middleware.rate_limit import (
    LOGIN_MAX_ATTEMPTS,
    check_login_rate_limit,
    record_login_attempt,
    reset_rate_limits_for_tests,
)
from app.models.enums import UserRole
from app.services import auth_service


def test_hash_and_verify_password_bcrypt_cost_12() -> None:
    hashed = auth_service.hash_password("secure-pass-123")
    assert hashed.startswith("$2")
    assert auth_service.verify_password("secure-pass-123", hashed) is True
    assert auth_service.verify_password("wrong", hashed) is False
    # bcrypt cost factor embedded as $2b$12$...
    assert "$12$" in hashed


def test_access_and_refresh_token_roundtrip() -> None:
    user_id = uuid.uuid4()
    access = auth_service.create_access_token(
        user_id=user_id,
        role=UserRole.buyer,
        email="buyer@example.com",
    )
    refresh = auth_service.create_refresh_token(user_id=user_id, role=UserRole.buyer)

    access_payload = auth_service.decode_access_token(access)
    refresh_payload = auth_service.decode_refresh_token(refresh)

    assert access_payload["sub"] == str(user_id)
    assert access_payload["role"] == "buyer"
    assert access_payload["type"] == "access"
    assert refresh_payload["type"] == "refresh"
    assert refresh_payload["sub"] == str(user_id)

    with pytest.raises(auth_service.AuthError):
        auth_service.decode_access_token(refresh)

    with pytest.raises(auth_service.AuthError):
        auth_service.decode_refresh_token(access)


def _fake_request(ip: str = "203.0.113.10") -> Request:
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/api/auth/login",
        "raw_path": b"/api/auth/login",
        "query_string": b"",
        "headers": [],
        "client": (ip, 12345),
        "server": ("test", 80),
    }
    return Request(scope)


def test_login_rate_limit_five_per_ip() -> None:
    reset_rate_limits_for_tests()
    req = _fake_request()
    for _ in range(LOGIN_MAX_ATTEMPTS):
        check_login_rate_limit(req)
        record_login_attempt(req)
    with pytest.raises(HTTPException) as exc_info:
        check_login_rate_limit(req)
    assert exc_info.value.status_code == 429
