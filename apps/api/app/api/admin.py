"""Admin domain API — disputes, suspend, CIS override entrypoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import CurrentUser, require_role
from app.domain_enums import BookingStatus, ListingStatus, UserRole
from app.repositories.memory_store import AuditLogRecord, new_id, store
from app.schemas.admin import (
    DisputeResolution,
    DisputeResolveRequest,
    DisputeResolveResponse,
    SuspendListingRequest,
)
from app.schemas.cis import CisOverrideRequest, CisScoreResponse
from app.schemas.listings import ListingResponse
from app.services import booking_service, cis_service, stripe_service
from app.services.booking_service import (
    BookingServiceError,
    InvalidTransitionError,
)
from app.services.cis_service import CisServiceError

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post(
    "/bookings/{booking_id}/resolve-dispute",
    response_model=DisputeResolveResponse,
)
async def resolve_dispute(
    booking_id: str,
    body: DisputeResolveRequest,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> DisputeResolveResponse:
    booking = store.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status != BookingStatus.DISPUTED:
        raise HTTPException(
            status_code=400,
            detail=f"Booking must be Disputed, got {booking.status.value}",
        )

    if body.resolution == DisputeResolution.PARTIAL_REFUND:
        if body.partial_percent is None:
            raise HTTPException(
                status_code=400,
                detail="partial_percent required for partial_refund",
            )
        # Partial: keep reduced transfer amount then Complete
        payout = int(
            round(
                (booking.total_pence - booking.commission_pence)
                * (body.partial_percent / 100)
            )
        )
        store.update_booking(
            booking_id,
            commission_pence=booking.total_pence - payout,
        )
        try:
            updated = booking_service.transition(
                booking_id,
                BookingStatus.COMPLETED,
                actor=f"admin:{user.id}",
            )
        except (BookingServiceError, InvalidTransitionError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        message = f"Partial payout {body.partial_percent}% approved"

    elif body.resolution == DisputeResolution.APPROVE_SELLER:
        try:
            updated = booking_service.transition(
                booking_id,
                BookingStatus.COMPLETED,
                actor=f"admin:{user.id}",
            )
        except (BookingServiceError, InvalidTransitionError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        message = "Seller approved — full payout"

    else:  # FULL_REFUND
        try:
            stripe_service.refund_payment(booking)
            updated = booking_service.transition(
                booking_id,
                BookingStatus.REFUNDED,
                actor=f"admin:{user.id}",
            )
        except (BookingServiceError, InvalidTransitionError, ValueError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        message = "Full refund issued"

    store.add_audit_log(
        AuditLogRecord(
            id=new_id(),
            actor_id=user.id,
            action="resolve_dispute",
            entity_type="booking",
            entity_id=booking_id,
            details={
                "resolution": body.resolution.value,
                "reason": body.reason,
                "partial_percent": body.partial_percent,
            },
        )
    )
    return DisputeResolveResponse(
        booking_id=updated.id,
        status=updated.status.value,
        message=message,
    )


@router.post("/listings/{listing_id}/suspend", response_model=ListingResponse)
async def suspend_listing(
    listing_id: str,
    body: SuspendListingRequest,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> ListingResponse:
    listing = store.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    updated = store.update_listing(
        listing_id, status=ListingStatus.SUSPENDED
    )
    assert updated is not None
    store.add_audit_log(
        AuditLogRecord(
            id=new_id(),
            actor_id=user.id,
            action="suspend_listing",
            entity_type="listing",
            entity_id=listing_id,
            details={"reason": body.reason},
        )
    )
    return ListingResponse(
        id=updated.id,
        seller_id=updated.seller_id,
        title=updated.title,
        description=updated.description,
        category=updated.category,
        status=updated.status,
        price_per_day_pence=updated.price_per_day_pence,
        lat=updated.lat,
        lng=updated.lng,
        images=updated.images,
        cis_score=updated.cis_score,
        is_cis_overridden=updated.is_cis_overridden,
        audience_tags=updated.audience_tags,
        booking_types=updated.booking_types,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.post(
    "/listings/{listing_id}/cis-override", response_model=CisScoreResponse
)
async def admin_cis_override(
    listing_id: str,
    body: CisOverrideRequest,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> CisScoreResponse:
    try:
        score = cis_service.apply_admin_override(
            listing_id=listing_id,
            cis_score=body.cis_score,
            admin_id=user.id,
            reason=body.reason,
        )
    except CisServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return CisScoreResponse(
        listing_id=listing_id,
        cis_score=score,
        is_cis_overridden=True,
        completed_bookings_counted=0,
    )
