"""
FastAPI entrypoint for Marketplays API (Vercel Python runtime expects `app`).

Import path: `app.main:app`
Entrypoint file: `app/main.py` (see pyproject.toml `[tool.vercel] entrypoint`).
If Vercel cannot resolve the nested package, symlink/copy:
  `ln -s app/main.py ./main.py` with project root `apps/api`.
"""

from __future__ import annotations

import os

from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.router import domain_router
from app.services import booking_service

app = FastAPI(
    title="Marketplays API",
    version="0.1.0",
    description="Auth + domain API — bookings, listings, payments, CIS",
)

_DEFAULT_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:3010",
    "https://marketplays.com",
    "https://www.marketplays.com",
    # Production / Vercel web project placeholders
    "https://marketplays-web.vercel.app",
]

_extra = os.getenv("CORS_ORIGINS", "")
_origins = list(_DEFAULT_ORIGINS)
if _extra.strip():
    _origins.extend(o.strip() for o in _extra.split(",") if o.strip())

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["auth"])
app.include_router(domain_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


def _assert_cron_secret(authorization: str | None) -> None:
    """Vercel Cron sends Authorization: Bearer <CRON_SECRET> when configured."""
    expected = os.getenv("CRON_SECRET")
    if not expected:
        # Local/dev: allow without secret; production must set CRON_SECRET
        return
    if authorization != f"Bearer {expected}":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid cron authorization",
        )


@app.get(
    "/api/cron/booking-transitions",
    summary="Run daily booking state-machine transitions",
    description=(
        "Cron (00:01 UTC): Confirmed→Live when start_date is reached, "
        "Live→Awaiting_Proof when end_date has passed, 48h Awaiting_Proof→"
        "Admin_Flagged, 72h Awaiting_Buyer_Review auto-approve (rating 3), "
        "and Pending_Payment 15-minute abandonment release."
    ),
)
async def cron_booking_transitions(
    authorization: str | None = Header(default=None),
) -> dict[str, str | int]:
    """Daily 00:01 UTC — Confirmed→Live, Live→Awaiting_Proof, timeouts, abandonment."""
    _assert_cron_secret(authorization)
    abandoned = booking_service.release_abandoned_pending_payment()
    daily = booking_service.run_daily_transitions()
    return {
        "status": "ok",
        "job": "booking-transitions",
        "abandoned_released": len(abandoned),
        "confirmed_to_live": daily["confirmed_to_live"],
        "live_to_awaiting_proof": daily["live_to_awaiting_proof"],
        "proof_timeout_flagged": daily["proof_timeout_flagged"],
        "reviews_auto_approved": daily["reviews_auto_approved"],
    }


@app.get("/api/cron/extend-availability")
async def cron_extend_availability(
    authorization: str | None = Header(default=None),
) -> dict[str, str]:
    """Daily — extend 90-day availability window (TODO: wire availability service)."""
    _assert_cron_secret(authorization)
    return {"status": "ok", "job": "extend-availability", "detail": "stub"}
