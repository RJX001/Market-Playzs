"""Auth service: register/login, bcrypt (cost 12), JWT access + refresh.

Uses shared `User` ORM from Database agent. Refresh tokens are issued for
HttpOnly cookies only — never returned in JSON response bodies.

Verification + password-reset tokens are purpose-bound JWTs (not access tokens).
Phone OTPs are hashed in-process (stub SMS via logging until a provider key exists).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
import os
import secrets
import uuid
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from threading import Lock
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
EMAIL_VERIFY_TTL = timedelta(hours=24)
PASSWORD_RESET_TTL = timedelta(hours=1)
PHONE_OTP_TTL = timedelta(minutes=10)
PHONE_OTP_MAX_ATTEMPTS = 5
PHONE_OTP_LENGTH = 6

REFRESH_COOKIE_NAME = "refresh_token"

TOKEN_TYPE_ACCESS = "access"
TOKEN_TYPE_REFRESH = "refresh"
TOKEN_TYPE_EMAIL_VERIFY = "email_verify"
TOKEN_TYPE_PASSWORD_RESET = "password_reset"

logger = logging.getLogger(__name__)


@dataclass
class _PhoneChallenge:
    code_hash: str
    expires_at: datetime
    attempts: int
    phone: str


_phone_lock = Lock()
_phone_challenges: dict[str, _PhoneChallenge] = {}


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


def _is_dev_env() -> bool:
    env = os.getenv("ENVIRONMENT", os.getenv("VERCEL_ENV", "development")).lower()
    return env in {"development", "dev", "local", "test", ""}


def _has_sendgrid_key() -> bool:
    return bool(os.getenv("SENDGRID_API_KEY", "").strip())


def _has_sms_provider_key() -> bool:
    return bool(
        os.getenv("TWILIO_AUTH_TOKEN", "").strip()
        or os.getenv("TWILIO_API_KEY", "").strip()
    )


def _hash_otp(code: str) -> str:
    return hmac.new(
        _jwt_secret().encode("utf-8"),
        code.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def generate_phone_otp() -> str:
    """6-digit numeric OTP. Tests may monkeypatch this."""
    return f"{secrets.randbelow(10**PHONE_OTP_LENGTH):0{PHONE_OTP_LENGTH}d}"


def reset_phone_challenges_for_tests() -> None:
    with _phone_lock:
        _phone_challenges.clear()


def _encode_purpose_token(
    *,
    user_id: uuid.UUID,
    token_type: str,
    ttl: timedelta,
    extra: dict[str, Any] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "type": token_type,
        "iat": now,
        "exp": now + ttl,
        "jti": str(uuid.uuid4()),
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, _jwt_secret(), algorithm="HS256")


def decode_purpose_token(token: str, *, expected_type: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(token, _jwt_secret(), algorithms=["HS256"])
    except jwt.PyJWTError as exc:
        raise AuthError("Invalid or expired token", status_code=400) from exc
    if payload.get("type") != expected_type:
        raise AuthError("Invalid token type", status_code=400)
    return payload


def create_email_verification_token(*, user_id: uuid.UUID, email: str) -> str:
    return _encode_purpose_token(
        user_id=user_id,
        token_type=TOKEN_TYPE_EMAIL_VERIFY,
        ttl=EMAIL_VERIFY_TTL,
        extra={"email": email},
    )


def create_password_reset_token(*, user_id: uuid.UUID, password_hash: str) -> str:
    # Bind token to current hash so a completed reset invalidates outstanding tokens.
    return _encode_purpose_token(
        user_id=user_id,
        token_type=TOKEN_TYPE_PASSWORD_RESET,
        ttl=PASSWORD_RESET_TTL,
        extra={"pwd": password_hash[:16]},
    )


def deliver_email_verification(email: str, token: str) -> None:
    """Stub SendGrid: log unless SENDGRID_API_KEY is set."""
    subject = "Verify your Marketplays email"
    logger.info("notify:email_verification to=%s subject=%s", email, subject)
    if _has_sendgrid_key():
        logger.info("notify:email_verification sendgrid queued to=%s", email)
        return
    if _is_dev_env():
        logger.info("notify:email_verification stub token=%s to=%s", token, email)
    else:
        logger.info("notify:email_verification stub (token omitted) to=%s", email)


def deliver_password_reset(email: str, token: str) -> None:
    """Stub SendGrid: log unless SENDGRID_API_KEY is set. Never log passwords."""
    subject = "Reset your Marketplays password"
    logger.info("notify:password_reset to=%s subject=%s", email, subject)
    if _has_sendgrid_key():
        logger.info("notify:password_reset sendgrid queued to=%s", email)
        return
    if _is_dev_env():
        logger.info("notify:password_reset stub token=%s to=%s", token, email)
    else:
        logger.info("notify:password_reset stub (token omitted) to=%s", email)


def deliver_phone_otp(phone: str, code: str) -> None:
    """Stub SMS: log unless Twilio key is set. Code logged only in dev/test."""
    logger.info("notify:phone_otp to=%s", phone)
    if _has_sms_provider_key():
        logger.info("notify:phone_otp twilio queued to=%s", phone)
        return
    if _is_dev_env():
        logger.info("notify:phone_otp stub code=%s to=%s", code, phone)
    else:
        logger.info("notify:phone_otp stub (code omitted) to=%s", phone)


def request_email_verification(db: Session, email: str) -> tuple[User, str] | None:
    """Return (user, token) if a verification email should be sent; else None.

    Unknown / suspended / already-verified emails return None so callers can
    always respond 200 (no account enumeration).
    """
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or user.is_suspended or user.email_verified_at is not None:
        return None
    token = create_email_verification_token(user_id=user.id, email=user.email)
    return user, token


def confirm_email_verification(db: Session, token: str) -> User:
    payload = decode_purpose_token(token, expected_type=TOKEN_TYPE_EMAIL_VERIFY)
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise AuthError("Invalid verification token", status_code=400) from exc

    user = db.get(User, user_id)
    if user is None:
        raise AuthError("Invalid verification token", status_code=400)
    if user.is_suspended:
        raise AuthError("Account is suspended", status_code=403)

    token_email = str(payload.get("email", "")).lower()
    if token_email and token_email != user.email.lower():
        raise AuthError("Invalid verification token", status_code=400)

    if user.email_verified_at is None:
        user.email_verified_at = datetime.now(UTC)
        db.commit()
        db.refresh(user)
    return user


def request_password_reset(db: Session, email: str) -> tuple[User, str] | None:
    """Return (user, token) if a reset email should be sent; else None."""
    user = db.scalar(select(User).where(User.email == email.lower()))
    if user is None or user.is_suspended:
        return None
    token = create_password_reset_token(
        user_id=user.id, password_hash=user.password_hash
    )
    return user, token


def confirm_password_reset(db: Session, token: str, new_password: str) -> User:
    payload = decode_purpose_token(token, expected_type=TOKEN_TYPE_PASSWORD_RESET)
    try:
        user_id = uuid.UUID(str(payload["sub"]))
    except (KeyError, ValueError) as exc:
        raise AuthError("Invalid reset token", status_code=400) from exc

    user = db.get(User, user_id)
    if user is None:
        raise AuthError("Invalid reset token", status_code=400)
    if user.is_suspended:
        raise AuthError("Account is suspended", status_code=403)
    if payload.get("pwd") != user.password_hash[:16]:
        raise AuthError("Invalid or already used reset token", status_code=400)

    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user


def request_phone_verification(
    db: Session, user: User, phone: str | None
) -> tuple[str, str]:
    """Store a hashed OTP and return (phone, code) for stub delivery."""
    target = (phone or user.phone or "").strip()
    if not target:
        raise AuthError("Phone number required", status_code=400)

    if user.phone != target:
        user.phone = target
        user.phone_verified = False
        db.commit()
        db.refresh(user)

    code = generate_phone_otp()
    challenge = _PhoneChallenge(
        code_hash=_hash_otp(code),
        expires_at=datetime.now(UTC) + PHONE_OTP_TTL,
        attempts=0,
        phone=target,
    )
    with _phone_lock:
        _phone_challenges[str(user.id)] = challenge
    return target, code


def confirm_phone_verification(db: Session, user: User, code: str) -> User:
    now = datetime.now(UTC)
    key = str(user.id)
    with _phone_lock:
        challenge = _phone_challenges.get(key)
        if challenge is None or challenge.expires_at < now:
            _phone_challenges.pop(key, None)
            raise AuthError("Invalid or expired verification code", status_code=400)
        if challenge.attempts >= PHONE_OTP_MAX_ATTEMPTS:
            raise AuthError(
                "Too many verification attempts. Request a new code.",
                status_code=429,
            )
        challenge.attempts += 1
        if not hmac.compare_digest(challenge.code_hash, _hash_otp(code.strip())):
            raise AuthError("Invalid or expired verification code", status_code=400)
        _phone_challenges.pop(key, None)

    user.phone_verified = True
    db.commit()
    db.refresh(user)
    return user
