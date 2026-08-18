"""Availability API — one row per date per listing.

Date locks are applied in ``booking_service.create_booking`` at PaymentIntent
creation and released on Cancelled/Refunded (including 15-minute
``release_abandoned_pending_payment``). This router stays read/ensure-window.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.repositories.memory_store import store
from app.schemas.availability import (
    AvailabilityDay,
    AvailabilityQueryResponse,
    AvailabilityWindowCreate,
)

router = APIRouter(prefix="/api/availability", tags=["availability"])


@router.get("/{listing_id}", response_model=AvailabilityQueryResponse)
async def get_availability(
    listing_id: str,
    start_date: date = Query(...),
    end_date: date = Query(...),
) -> AvailabilityQueryResponse:
    if end_date < start_date:
        raise HTTPException(
            status_code=400, detail="end_date must be on or after start_date"
        )
    listing = store.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    days = store.get_availability_for_range(listing_id, start_date, end_date)
    return AvailabilityQueryResponse(
        listing_id=listing_id,
        start_date=start_date,
        end_date=end_date,
        days=[
            AvailabilityDay(
                id=d.id,
                listing_id=d.listing_id,
                day=d.day,
                is_locked=d.is_locked,
                booking_id=d.booking_id,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in days
        ],
    )


@router.post("/{listing_id}/window", response_model=AvailabilityQueryResponse)
async def ensure_availability_window(
    listing_id: str,
    body: AvailabilityWindowCreate,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> AvailabilityQueryResponse:
    listing = store.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if listing.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if body.end_date < body.start_date:
        raise HTTPException(
            status_code=400, detail="end_date must be on or after start_date"
        )

    store.ensure_availability_window(
        listing_id, body.start_date, body.end_date
    )
    days = store.get_availability_for_range(
        listing_id, body.start_date, body.end_date
    )
    return AvailabilityQueryResponse(
        listing_id=listing_id,
        start_date=body.start_date,
        end_date=body.end_date,
        days=[
            AvailabilityDay(
                id=d.id,
                listing_id=d.listing_id,
                day=d.day,
                is_locked=d.is_locked,
                booking_id=d.booking_id,
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in days
        ],
    )
