"""Auth routes: register, login, refresh, logout, verification, password reset.

Live JWT/bcrypt provider — do not remove until Clerk cutover
(docs/clerk-migration-plan.md). Roadmap Phase 1.1 targets Clerk as IdP;
Section 5.1 RBAC/rate-limit principles still apply here.
"""

from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser, require_role
from app.db.session import get_db
from app.domain_enums import UserRole
from app.middleware.rate_limit import check_login_rate_limit, record_login_attempt
from app.schemas.auth import (
    AccessTokenResponse,
    EmailVerifyConfirmRequest,
    EmailVerifyRequest,
    LoginRequest,
    MessageResponse,
    PasswordResetConfirmRequest,
    PasswordResetRequest,
    PhoneVerifyConfirmRequest,
    PhoneVerifyRequest,
    RegisterRequest,
    UserResponse,
)
from app.services import auth_service
from app.services.auth_service import REFRESH_COOKIE_NAME, AuthError

router = APIRouter()

_ANY_ROLE = require_role(UserRole.BUYER, UserRole.SELLER, UserRole.ADMIN)


def _set_refresh_cookie(response: Response, refresh_token: str) -> None:
    response.set_cookie(
        key=REFRESH_COOKIE_NAME,
        value=refresh_token,
        httponly=True,
        secure=auth_service.cookie_secure(),
        samesite="lax",
        max_age=int(auth_service.REFRESH_TOKEN_TTL.total_seconds()),
        path="/api/auth",
    )


def _clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        key=REFRESH_COOKIE_NAME,
        path="/api/auth",
        httponly=True,
        secure=auth_service.cookie_secure(),
        samesite="lax",
    )


def _token_response(user: object, access_token: str) -> AccessTokenResponse:
    return AccessTokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=auth_service.ACCESS_TOKEN_EXPIRES_SECONDS,
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/register",
    response_model=AccessTokenResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    body: RegisterRequest,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AccessTokenResponse:
    try:
        user, access, refresh = auth_service.register_user(db, body)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    _set_refresh_cookie(response, refresh)
    return _token_response(user, access)


@router.post("/login", response_model=AccessTokenResponse)
async def login(
    body: LoginRequest,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AccessTokenResponse:
    check_login_rate_limit(request)
    record_login_attempt(request)
    try:
        user, access, refresh = auth_service.authenticate_user(db, body)
    except AuthError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    _set_refresh_cookie(response, refresh)
    return _token_response(user, access)


@router.post("/refresh", response_model=AccessTokenResponse)
async def refresh(
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> AccessTokenResponse:
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing refresh token cookie",
        )
    try:
        user, access, new_refresh = auth_service.refresh_tokens(db, refresh_token)
    except AuthError as exc:
        _clear_refresh_cookie(response)
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc
    _set_refresh_cookie(response, new_refresh)
    return _token_response(user, access)


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response) -> MessageResponse:
    _clear_refresh_cookie(response)
    return MessageResponse(message="Logged out")


def _auth_http_error(exc: AuthError) -> HTTPException:
    return HTTPException(status_code=exc.status_code, detail=exc.message)


@router.post(
    "/verify-email/request",
    response_model=MessageResponse,
    summary="Request email verification",
    description=(
        "Send a time-limited email verification token to the given address. "
        "Always returns 200 with a generic message so callers cannot enumerate accounts. "
        "Delivery is stubbed via logging unless SENDGRID_API_KEY is configured."
    ),
)
async def request_email_verification(
    body: EmailVerifyRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    check_login_rate_limit(request)
    record_login_attempt(request)
    pending = auth_service.request_email_verification(db, body.email)
    if pending is not None:
        user, token = pending
        background_tasks.add_task(
            auth_service.deliver_email_verification, user.email, token
        )
    return MessageResponse(
        message="If an account exists for that email, a verification link has been sent"
    )


@router.post(
    "/verify-email/confirm",
    response_model=MessageResponse,
    summary="Confirm email verification",
    description=(
        "Consume an email verification token issued by POST /api/auth/verify-email/request "
        "and set email_verified_at on the user. Idempotent if the address is already verified."
    ),
)
async def confirm_email_verification(
    body: EmailVerifyConfirmRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    try:
        auth_service.confirm_email_verification(db, body.token)
    except AuthError as exc:
        raise _auth_http_error(exc) from exc
    return MessageResponse(message="Email verified")


@router.post(
    "/password-reset/request",
    response_model=MessageResponse,
    summary="Request password reset",
    description=(
        "Send a time-limited password-reset token to the given address. "
        "Always returns 200 with a generic message so callers cannot enumerate accounts. "
        "Rate-limited per IP (same window as login). Delivery is stubbed via logging "
        "unless SENDGRID_API_KEY is configured. Never returns password hints."
    ),
)
async def request_password_reset(
    body: PasswordResetRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    check_login_rate_limit(request)
    record_login_attempt(request)
    pending = auth_service.request_password_reset(db, body.email)
    if pending is not None:
        user, token = pending
        background_tasks.add_task(auth_service.deliver_password_reset, user.email, token)
    return MessageResponse(
        message="If an account exists for that email, a reset link has been sent"
    )


@router.post(
    "/password-reset/confirm",
    response_model=MessageResponse,
    summary="Confirm password reset",
    description=(
        "Set a new password using a token from POST /api/auth/password-reset/request. "
        "The token is bound to the current password hash and cannot be reused after a "
        "successful reset. Access/refresh cookies are not issued here — the user must log in."
    ),
)
async def confirm_password_reset(
    body: PasswordResetConfirmRequest,
    db: Annotated[Session, Depends(get_db)],
) -> MessageResponse:
    try:
        auth_service.confirm_password_reset(db, body.token, body.new_password)
    except AuthError as exc:
        raise _auth_http_error(exc) from exc
    return MessageResponse(message="Password reset successful")


@router.post(
    "/verify-phone/request",
    response_model=MessageResponse,
    summary="Request phone verification",
    description=(
        "Authenticated buyer/seller/admin: send a 6-digit OTP to the user's phone. "
        "Optional body.phone updates the stored number and clears phone_verified. "
        "SMS is stubbed via logging unless a Twilio key is configured."
    ),
)
async def request_phone_verification(
    body: PhoneVerifyRequest,
    background_tasks: BackgroundTasks,
    db: Annotated[Session, Depends(get_db)],
    current: CurrentUser = Depends(_ANY_ROLE),
) -> MessageResponse:
    user = auth_service.get_user_by_id(db, UUID(current.id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    try:
        phone, code = auth_service.request_phone_verification(db, user, body.phone)
    except AuthError as exc:
        raise _auth_http_error(exc) from exc
    background_tasks.add_task(auth_service.deliver_phone_otp, phone, code)
    return MessageResponse(message="A verification code has been sent")


@router.post(
    "/verify-phone/confirm",
    response_model=MessageResponse,
    summary="Confirm phone verification",
    description=(
        "Authenticated buyer/seller/admin: submit the OTP from "
        "POST /api/auth/verify-phone/request. Sets phone_verified on success."
    ),
)
async def confirm_phone_verification(
    body: PhoneVerifyConfirmRequest,
    db: Annotated[Session, Depends(get_db)],
    current: CurrentUser = Depends(_ANY_ROLE),
) -> MessageResponse:
    user = auth_service.get_user_by_id(db, UUID(current.id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    try:
        auth_service.confirm_phone_verification(db, user, body.code)
    except AuthError as exc:
        raise _auth_http_error(exc) from exc
    return MessageResponse(message="Phone verified")
