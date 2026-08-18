"""B11 — per-booking QR/promo attribution codes and public scan redirect."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.repositories.memory_store import store

router = APIRouter(tags=["attribution"])


class AttributionResponse(BaseModel):
    booking_id: str
    code: str
    redirect_url: str
    target_url: str
    scan_count: int
    redemption_count: int


def _assert_booking_access(booking, user: CurrentUser) -> None:
    if user.role == UserRole.ADMIN:
        return
    if user.role == UserRole.BUYER and booking.buyer_id == user.id:
        return
    if user.role == UserRole.SELLER and booking.seller_id == user.id:
        return
    raise HTTPException(status_code=403, detail="Forbidden")


@router.get(
    "/api/bookings/{booking_id}/attribution",
    response_model=AttributionResponse,
    summary="Get booking attribution code",
    description=(
        "Buyer, seller, or admin for this booking. Returns the unique QR/promo "
        "code generated at booking creation, plus scan and redemption counts."
    ),
)
async def get_booking_attribution(
    booking_id: str,
    user: CurrentUser = Depends(
        require_role(UserRole.BUYER, UserRole.SELLER, UserRole.ADMIN)
    ),
) -> AttributionResponse:
    booking = store.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    _assert_booking_access(booking, user)
    rec = store.get_attribution_for_booking(booking_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Attribution not found")
    return AttributionResponse(
        booking_id=rec.booking_id,
        code=rec.code,
        redirect_url=f"/api/attribution/r/{rec.code}",
        target_url=rec.target_url,
        scan_count=rec.scan_count,
        redemption_count=rec.redemption_count,
    )


@router.get(
    "/api/attribution/r/{code}",
    summary="Record attribution scan and redirect",
    description=(
        "Public. Increments scan_count for the promo/QR code then redirects "
        "to the buyer target URL (defaults to https://marketplays.com)."
    ),
    response_class=RedirectResponse,
    status_code=302,
)
async def attribution_redirect(code: str) -> RedirectResponse:
    rec = store.record_attribution_scan(code)
    if not rec:
        raise HTTPException(status_code=404, detail="Attribution code not found")
    return RedirectResponse(url=rec.target_url, status_code=302)
