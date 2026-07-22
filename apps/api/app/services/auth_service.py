"""Auth service: register/login, bcrypt (cost 12), JWT access + refresh.

Uses shared `User` ORM from Database agent. Refresh tokens are issued for
HttpOnly cookies only — never returned in JSON response bodies.
"""

from __future__ import annotations

import os
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.enums import UserRole
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest

BCRYPT_ROUNDS = 12
ACCESS_TOKEN_TTL = timedelta(minutes=15)
REFRESH_TOKEN_TTL = timedelta(days=7)
ACCESS_TOKEN_EXPIRES_SECONDS = int(ACCESS_TOKEN_TTL.total_seconds())

REFRESH_COOKIE_NAME = "refresh_token"


class AuthError(Exception):
    """Domain auth failure with HTTP-friendly message."""

    def __init__(self, message: str, *, status_code: int = 401) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _jwt_secret() -> str:
    secret = os.getenv("JWT_SECRET", "").strip()
    if not secret:
        # Dev fallback (≥32 bytes) — production must set JWT_SECRET
        return "dev-jwt-secret-change-me-min-32b"
    return secret


def _jwt_refresh_secret() -> str:
    secret = os.getenv("JWT_REFRESH_SECRET", "").strip()
    if not secret:
        return "dev-jwt-refresh-secret-change-me-32b"
    return secret


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=BCRYPT_ROUNDS))
    return hashed.decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except (ValueError, TypeError):
        return False


def create_access_token(*, user_id: uuid.UUID, role: UserRole, email: str) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "email": email,
        "type": "access",
        "iat": now,
        "exp": now + ACCESS_TOKEN_TTL,
    }
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def create_refresh_token(*, user_id: uuid.UUID, role: UserRole) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role.value,
        "type": "refresh",
        "iat": now,
        "exp": now + REFRESH_TOKEN_TTL,
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, _jwt_refresh_secret(), algorithm="HS256")


def decode_access_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid or expired access token") from exc
    if payload.get("type") != "access":
        raise AuthError("Invalid access token type")
    return payload


def decode_refresh_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _jwt_refresh_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid or expired refresh token") from exc
    if payload.get("type") != "refresh":
        raise AuthError("Invalid refresh token type")
    return payload


def register_user(db: Session, body: RegisterRequest) -> tuple[User, str, str]:
    """Create user; returns (user, access_token, refresh_token)."""
    existing = db.scalar(select(User).where(User.email == body.email.lower()))
    if existing is not None:
        raise AuthError("Email already registered", status_code=409)

    role = UserRole(body.role)
    if role == UserRole.admin:
        raise AuthError("Cannot self-register as admin", status_code=400)

    user = User(
        email=body.email.lower(),
        password_hash=hash_password(body.password),
        role=role,
        full_name=body.full_name.strip(),
        company_name=body.company_name,
        phone=body.phone,
        is_suspended=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access = create_access_token(user_id=user.id, role=user.role, email=user.email)
    refresh = create_refresh_token(user_id=user.id, role=user.role)
    return user, access, refresh


def authenticate_user(db: Session, body: LoginRequest) -> tuple[User, str, str]:
    """Validate credentials; returns (user, access_token, refresh_token)."""
    user = db.scalar(select(User).where(User.email == body.email.lower()))
    # Constant-ish failure message — never leak whether email exists or password hints.
    if user is None or not verify_password(body.password, user.password_hash):
        raise AuthError("Invalid email or password", status_code=401)
    if user.is_suspended:
        raise AuthError("Account is suspended", status_code=403)

    access = create_access_token(user_id=user.id, role=user.role, email=user.email)
    refresh = create_refresh_token(user_id=user.id, role=user.role)
    return user, access, refresh


def refresh_tokens(db: Session, refresh_token: str) -> tuple[User, str, str]:
    """Rotate access (+ refresh) from a valid refresh cookie token."""
    payload = decode_refresh_token(refresh_token)
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise AuthError("Invalid refresh token subject") from exc

    user = db.get(User, user_id)
    if user is None:
        raise AuthError("User not found", status_code=401)
    if user.is_suspended:
        raise AuthError("Account is suspended", status_code=403)

    access = create_access_token(user_id=user.id, role=user.role, email=user.email)
    new_refresh = create_refresh_token(user_id=user.id, role=user.role)
    return user, access, new_refresh


def get_user_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    return db.get(User, user_id)


def cookie_secure() -> bool:
    """Secure flag for refresh cookie — true outside local development."""
    env = os.getenv("ENVIRONMENT", os.getenv("VERCEL_ENV", "development")).lower()
    return env in {"production", "preview", "prod"}
