"""Unit tests for auth service (password + JWT) and rate limits — no DB required.

New verification / password-reset flows use TestClient + in-memory SQLite.
"""

from __future__ import annotations

import uuid
from collections.abc import Generator

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from starlette.requests import Request

from app.db.session import get_db
from app.main import app
from app.middleware.rate_limit import (
    LOGIN_MAX_ATTEMPTS,
    check_login_rate_limit,
    record_login_attempt,
    reset_rate_limits_for_tests,
)
from app.models.audit_log import AuditLog  # noqa: F401
from app.models.availability import Availability  # noqa: F401
from app.models.booking import Booking  # noqa: F401
from app.models.buyer_agent_policy import BuyerAgentPolicy  # noqa: F401
from app.models.deliverable import Deliverable  # noqa: F401
from app.models.enums import UserRole
from app.models.listing import Listing  # noqa: F401
from app.models.review import Review  # noqa: F401
from app.models.user import User
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


def test_purpose_tokens_reject_access_jwt() -> None:
    user_id = uuid.uuid4()
    access = auth_service.create_access_token(
        user_id=user_id, role=UserRole.buyer, email="buyer@example.com"
    )
    email_token = auth_service.create_email_verification_token(
        user_id=user_id, email="buyer@example.com"
    )
    reset_token = auth_service.create_password_reset_token(
        user_id=user_id, password_hash="$2b$12$placeholderhashxx"
    )

    with pytest.raises(auth_service.AuthError):
        auth_service.decode_purpose_token(access, expected_type="email_verify")
    with pytest.raises(auth_service.AuthError):
        auth_service.decode_purpose_token(email_token, expected_type="password_reset")
    with pytest.raises(auth_service.AuthError):
        auth_service.decode_access_token(reset_token)

    payload = auth_service.decode_purpose_token(
        email_token, expected_type="email_verify"
    )
    assert payload["sub"] == str(user_id)
    assert payload["email"] == "buyer@example.com"


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


_REGISTER_BODY = {
    "email": "buyer@example.com",
    "password": "secure-pass-123",
    "full_name": "Buyer One",
    "role": "buyer",
    "phone": "+447700900123",
}


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
        class_=Session,
    )
    # Users table only — listings use PostGIS and are out of this workstream.
    User.__table__.create(bind=engine, checkfirst=True)

    def _override_get_db() -> Generator[Session, None, None]:
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = _override_get_db
    reset_rate_limits_for_tests()
    auth_service.reset_phone_challenges_for_tests()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    auth_service.reset_phone_challenges_for_tests()
    reset_rate_limits_for_tests()
    User.__table__.drop(bind=engine, checkfirst=True)
    engine.dispose()


def _auth_header(access_token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {access_token}"}


def test_register_and_login_still_work(client: TestClient) -> None:
    created = client.post("/api/auth/register", json=_REGISTER_BODY)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == "buyer@example.com"
    assert body["user"]["phone_verified"] is False
    assert body["user"]["email_verified_at"] is None

    login = client.post(
        "/api/auth/login",
        json={"email": "buyer@example.com", "password": "secure-pass-123"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["user"]["id"] == body["user"]["id"]


def test_email_verification_request_and_confirm(client: TestClient) -> None:
    created = client.post("/api/auth/register", json=_REGISTER_BODY)
    assert created.status_code == 201
    user_id = uuid.UUID(created.json()["user"]["id"])

    requested = client.post(
        "/api/auth/verify-email/request",
        json={"email": "buyer@example.com"},
    )
    assert requested.status_code == 200
    assert "verification" in requested.json()["message"].lower()

    unknown = client.post(
        "/api/auth/verify-email/request",
        json={"email": "nobody@example.com"},
    )
    assert unknown.status_code == 200

    token = auth_service.create_email_verification_token(
        user_id=user_id, email="buyer@example.com"
    )
    confirmed = client.post(
        "/api/auth/verify-email/confirm", json={"token": token}
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["message"] == "Email verified"

    again = client.post("/api/auth/verify-email/confirm", json={"token": token})
    assert again.status_code == 200


def test_email_verification_rejects_access_token(client: TestClient) -> None:
    created = client.post("/api/auth/register", json=_REGISTER_BODY)
    access = created.json()["access_token"]
    bad = client.post("/api/auth/verify-email/confirm", json={"token": access})
    assert bad.status_code == 400


def test_password_reset_request_and_confirm(client: TestClient) -> None:
    created = client.post("/api/auth/register", json=_REGISTER_BODY)
    assert created.status_code == 201
    user_id = uuid.UUID(created.json()["user"]["id"])

    requested = client.post(
        "/api/auth/password-reset/request",
        json={"email": "buyer@example.com"},
    )
    assert requested.status_code == 200

    unknown = client.post(
        "/api/auth/password-reset/request",
        json={"email": "ghost@example.com"},
    )
    assert unknown.status_code == 200

    override = app.dependency_overrides.get(get_db)
    assert override is not None
    db = next(override())
    try:
        user = db.get(User, user_id)
        assert user is not None
        token = auth_service.create_password_reset_token(
            user_id=user.id, password_hash=user.password_hash
        )
    finally:
        db.close()

    confirmed = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": "new-pass-4567"},
    )
    assert confirmed.status_code == 200, confirmed.text

    old_login = client.post(
        "/api/auth/login",
        json={"email": "buyer@example.com", "password": "secure-pass-123"},
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/auth/login",
        json={"email": "buyer@example.com", "password": "new-pass-4567"},
    )
    assert new_login.status_code == 200, new_login.text

    reused = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": token, "new_password": "another-pass-89"},
    )
    assert reused.status_code == 400


def test_phone_verification_request_and_confirm(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(auth_service, "generate_phone_otp", lambda: "123456")
    created = client.post("/api/auth/register", json=_REGISTER_BODY)
    assert created.status_code == 201
    access = created.json()["access_token"]
    assert created.json()["user"]["phone_verified"] is False

    requested = client.post(
        "/api/auth/verify-phone/request",
        headers=_auth_header(access),
        json={},
    )
    assert requested.status_code == 200, requested.text

    unauth = client.post("/api/auth/verify-phone/request", json={})
    assert unauth.status_code == 401

    confirmed = client.post(
        "/api/auth/verify-phone/confirm",
        headers=_auth_header(access),
        json={"code": "123456"},
    )
    assert confirmed.status_code == 200, confirmed.text

    login = client.post(
        "/api/auth/login",
        json={"email": "buyer@example.com", "password": "secure-pass-123"},
    )
    assert login.status_code == 200
    assert login.json()["user"]["phone_verified"] is True
    assert login.json()["user"]["phone"] == "+447700900123"


def test_phone_verification_requires_phone(
    client: TestClient,
) -> None:
    body = {**_REGISTER_BODY, "email": "nophone@example.com"}
    body.pop("phone")
    created = client.post("/api/auth/register", json=body)
    assert created.status_code == 201
    access = created.json()["access_token"]

    missing = client.post(
        "/api/auth/verify-phone/request",
        headers=_auth_header(access),
        json={},
    )
    assert missing.status_code == 400
