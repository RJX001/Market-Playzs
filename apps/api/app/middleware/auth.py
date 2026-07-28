"""JWT role middleware / FastAPI dependencies.

Buyer endpoints: buyer role only.
Seller endpoints: seller role only.
Admin endpoints: admin role only.

Live path: HS256 access JWT (auth_service). Domain routers typically use
app.api.deps.require_role instead — keep both in sync until Clerk cutover.
Clerk stub: app.services.clerk_compat — docs/clerk-migration-plan.md.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.middleware.rate_limit import check_user_rate_limit
from app.models.enums import UserRole
from app.services import auth_service

_bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: uuid.UUID
    email: str
    role: UserRole


async def get_current_user(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(_bearer),
    ],
    db: Annotated[Session, Depends(get_db)],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = auth_service.decode_access_token(credentials.credentials)
        user_id = uuid.UUID(str(payload["sub"]))
        role = UserRole(str(payload["role"]))
        email = str(payload["email"])
    except (auth_service.AuthError, KeyError, ValueError) as exc:
        detail = getattr(exc, "message", "Invalid or expired access token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Global authenticated rate limit (100/min) — Section 5.1
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

    return AuthenticatedUser(id=user.id, email=email, role=role)


def require_roles(*allowed: UserRole) -> Callable[..., AuthenticatedUser]:
    """Dependency factory: enforce role claim on protected routes."""

    allowed_set = set(allowed)

    async def _dependency(
        current: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if current.role not in allowed_set:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for this resource",
            )
        return current

    return _dependency


# Convenience aliases for other agents' routers
RequireBuyer = Annotated[AuthenticatedUser, Depends(require_roles(UserRole.buyer))]
RequireSeller = Annotated[AuthenticatedUser, Depends(require_roles(UserRole.seller))]
RequireAdmin = Annotated[AuthenticatedUser, Depends(require_roles(UserRole.admin))]
RequireAuth = Annotated[AuthenticatedUser, Depends(get_current_user)]
