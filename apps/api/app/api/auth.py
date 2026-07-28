"""Auth routes: register, login, refresh, logout.

Live JWT/bcrypt provider — do not remove until Clerk cutover
(docs/clerk-migration-plan.md). Roadmap Phase 1.1 targets Clerk as IdP;
Section 5.1 RBAC/rate-limit principles still apply here.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.rate_limit import check_login_rate_limit, record_login_attempt
from app.schemas.auth import (
    AccessTokenResponse,
    LoginRequest,
    MessageResponse,
    RegisterRequest,
    UserResponse,
)
from app.services import auth_service
from app.services.auth_service import REFRESH_COOKIE_NAME, AuthError

router = APIRouter()


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
