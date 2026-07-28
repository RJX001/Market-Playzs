"""Clerk compatibility stub — TODOs only until CLERK_* env keys are configured.

See docs/clerk-migration-plan.md.

Do NOT delete JWT/bcrypt paths in auth_service.py until cutover.
Section 5.1 RBAC/rate-limit principles still apply; provider becomes Clerk.
Booking state machine / CIS / schema are unchanged by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

# TODO(clerk): import clerk Backend SDK / PyJWKClient when implementing verification.


@dataclass(frozen=True, slots=True)
class ClerkIdentity:
    """Normalized identity from a verified Clerk session/JWT."""

    clerk_user_id: str
    email: str | None = None
    # Optional metadata from Clerk (never trust for authz without DB check)
    claimed_role: str | None = None


@dataclass(frozen=True, slots=True)
class LocalAuthUser:
    """Shape compatible with deps.CurrentUser / middleware AuthenticatedUser."""

    id: UUID
    email: str
    role: str  # buyer | seller | admin — always from DB after resolve


def clerk_configured() -> bool:
    """Return True when server-side Clerk secrets are present."""
    # TODO(clerk): check CLERK_SECRET_KEY (and issuer) without logging values.
    return False


def verify_clerk_bearer(token: str) -> ClerkIdentity:
    """Verify Authorization Bearer token as a Clerk session/JWT.

    TODO(clerk):
    - Fetch JWKS from CLERK_JWT_ISSUER
    - Validate signature, exp, azp / authorized party
    - Map claims → ClerkIdentity (sub → clerk_user_id)
    - Raise AuthError-equivalent on failure
    """
    raise NotImplementedError(
        "Clerk verification not implemented — set CLERK_* keys and implement "
        "verify_clerk_bearer (see docs/clerk-migration-plan.md)"
    )


def ensure_local_user(
    db: Session,
    identity: ClerkIdentity,
    *,
    signup_role: str | None = None,
) -> Any:
    """Map Clerk identity to local `users` row (create/link on first login).

    TODO(clerk):
    - Lookup by clerk_user_id (additive column) or email bridge during migration
    - On create: set role from signup_role (buyer|seller only; never admin)
    - Respect is_suspended on subsequent calls
    - Do not invent booking/CIS fields here
    """
    raise NotImplementedError("ensure_local_user TODO — see docs/clerk-migration-plan.md")


def resolve_authenticated_user(
    db: Session,
    bearer_token: str,
) -> LocalAuthUser:
    """Dual-mode resolver entrypoint for future deps.get_current_user.

    TODO(clerk):
    1. If clerk_configured(): verify_clerk_bearer → ensure_local_user → LocalAuthUser
    2. Else: fall back to auth_service.decode_access_token (existing JWT)
    3. Apply check_user_rate_limit(str(user.id)) in the FastAPI dep (unchanged)
    4. Keep require_role(...) call sites untouched
    """
    _ = (db, bearer_token)
    raise NotImplementedError(
        "resolve_authenticated_user TODO — JWT remains live via auth_service "
        "until this dual-mode path is wired (docs/clerk-migration-plan.md)"
    )
