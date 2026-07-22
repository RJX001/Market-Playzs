"""
Auth dependencies for role guards on protected routes.

Resolves Bearer JWT via Auth middleware (15min access). Refresh stays
HttpOnly-cookie-only on /api/auth/refresh — never accepted here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.domain_enums import UserRole
from app.middleware.rate_limit import check_user_rate_limit
from app.services import auth_service

_bearer = HTTPBearer(auto_error=False)


@dataclass
class CurrentUser:
    id: str
    role: UserRole
    email: str = ""


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> CurrentUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = auth_service.decode_access_token(credentials.credentials)
        user_id = UUID(str(payload["sub"]))
        role = UserRole(str(payload["role"]).lower())
        email = str(payload.get("email", ""))
    except (auth_service.AuthError, KeyError, ValueError) as exc:
        detail = getattr(exc, "message", "Invalid or expired access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    check_user_rate_limit(str(user_id))

    user = auth_service.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.is_suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is suspended",
        )

    return CurrentUser(id=str(user.id), role=role, email=email or user.email)


def require_role(*roles: UserRole):
    allowed = frozenset(roles)

    async def _dependency(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role: {', '.join(r.value for r in roles)}",
            )
        return user

    return _dependency
