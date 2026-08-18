"""Admin domain API — disputes, suspend, CIS override entrypoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import CurrentUser, require_role
from app.domain_enums import BookingStatus, ListingStatus, UserRole
from app.repositories.memory_store import (
    DISPUTE_SLA_THRESHOLD_PENCE,
    AuditLogRecord,
    new_id,
    store,
)
from app.schemas.admin import (
    AdminReportResponse,
    AuditLogItem,
    AuditLogListResponse,
    DisputeListItem,
    DisputeListResponse,
    DisputeResolution,
    DisputeResolveRequest,
    DisputeResolveResponse,
    ModerationListingItem,
    ModerationQueueResponse,
    ModerationRejectRequest,
    SuspendListingRequest,
)
from app.schemas.cis import CisOverrideRequest, CisScoreResponse
from app.schemas.listings import ListingResponse
from app.services import analytics_service, booking_service, cis_service, stripe_service
from app.services.booking_service import (
    BookingServiceError,
    InvalidTransitionError,
)
from app.services.cis_service import CisServiceError

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _listing_response(listing) -> ListingResponse:
    return ListingResponse(
        id=listing.id,
        seller_id=listing.seller_id,
        title=listing.title,
        description=listing.description,
        category=listing.category,
        status=listing.status,
        price_per_day_pence=listing.price_per_day_pence,
        lat=listing.lat,
        lng=listing.lng,
        images=listing.images,
        cis_score=listing.cis_score,
        is_cis_overridden=listing.is_cis_overridden,
        audience_tags=listing.audience_tags,
        booking_types=listing.booking_types,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


def _write_audit(
    user: CurrentUser,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict,
) -> None:
    store.add_audit_log(
        AuditLogRecord(
            id=new_id(),
            actor_id=user.id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
        )
    )


@router.post(
    "/bookings/{booking_id}/resolve-dispute",
    response_model=DisputeResolveResponse,
    summary="Resolve a disputed booking",
    description=(
        "Exactly three paths: approve_seller (Completed, full payout), "
        "full_refund (Refunded), partial_refund (Completed with reduced payout). "
        "Writes an audit_logs row."
    ),
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


@router.post(
    "/listings/{listing_id}/suspend",
    response_model=ListingResponse,
    summary="Suspend a listing",
    description="Removes the listing from buyer queries. Writes an audit_logs row.",
)
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
    "/listings/{listing_id}/cis-override",
    response_model=CisScoreResponse,
    summary="Override listing CIS score",
    description=(
        "Sets is_cis_overridden and writes an audit_logs row via cis_service."
    ),
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


@router.get(
    "/audit-logs",
    response_model=AuditLogListResponse,
    summary="List admin audit logs",
    description="Filterable by actor, action, entity type, and entity id. Newest first.",
)
async def list_audit_logs(
    actor_id: str | None = Query(default=None),
    action: str | None = Query(default=None),
    entity_type: str | None = Query(default=None),
    entity_id: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> AuditLogListResponse:
    del user
    rows = store.list_audit_logs(
        actor_id=actor_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
    )
    total = len(rows)
    start = (page - 1) * page_size
    page_rows = rows[start : start + page_size]
    return AuditLogListResponse(
        items=[
            AuditLogItem(
                id=r.id,
                actor_id=r.actor_id,
                action=r.action,
                entity_type=r.entity_type,
                entity_id=r.entity_id,
                details=r.details,
                initiated_by_agent=r.initiated_by_agent,
                agent_session_id=r.agent_session_id,
                created_at=r.created_at,
            )
            for r in page_rows
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/moderation",
    response_model=ModerationQueueResponse,
    include_in_schema=False,
)
@router.get(
    "/moderation/listings",
    response_model=ModerationQueueResponse,
    summary="Listing moderation queue",
    description="Listings awaiting admin approve/reject (`moderation_status=pending`).",
)
async def list_moderation_queue(
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> ModerationQueueResponse:
    del user
    items = [
        ModerationListingItem(
            id=listing.id,
            seller_id=listing.seller_id,
            title=listing.title,
            category=listing.category.value,
            status=listing.status.value,
            moderation_status=listing.moderation_status,
            created_at=listing.created_at,
            updated_at=listing.updated_at,
        )
        for listing in store.list_listings()
        if listing.moderation_status == "pending"
    ]
    items.sort(key=lambda i: i.created_at)
    return ModerationQueueResponse(items=items)


@router.post(
    "/listings/{listing_id}/approve",
    response_model=ListingResponse,
    summary="Approve a listing",
    description="Sets moderation_status=approved, publishes the listing, writes audit_logs.",
)
async def approve_listing(
    listing_id: str,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> ListingResponse:
    listing = store.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    updated = store.update_listing(
        listing_id,
        moderation_status="approved",
        status=ListingStatus.PUBLISHED,
    )
    assert updated is not None
    _write_audit(
        user,
        action="approve_listing",
        entity_type="listing",
        entity_id=listing_id,
        details={"previous_status": listing.status.value},
    )
    return _listing_response(updated)


@router.post(
    "/listings/{listing_id}/reject",
    response_model=ListingResponse,
    summary="Reject a listing",
    description="Sets moderation_status=rejected, suspends the listing, writes audit_logs.",
)
async def reject_listing(
    listing_id: str,
    body: ModerationRejectRequest,
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> ListingResponse:
    listing = store.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    updated = store.update_listing(
        listing_id,
        moderation_status="rejected",
        status=ListingStatus.SUSPENDED,
    )
    assert updated is not None
    _write_audit(
        user,
        action="reject_listing",
        entity_type="listing",
        entity_id=listing_id,
        details={"reason": body.reason, "previous_status": listing.status.value},
    )
    return _listing_response(updated)


@router.get(
    "/disputes",
    response_model=DisputeListResponse,
    summary="List open disputes",
    description=(
        "Bookings in Disputed status with first_decision_due_at (72h SLA from "
        "creation, under the £500 value threshold)."
    ),
)
async def list_disputes(
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> DisputeListResponse:
    del user
    pairs = store.list_open_disputes()
    return DisputeListResponse(
        items=[
            DisputeListItem(
                booking_id=booking.id,
                listing_id=booking.listing_id,
                buyer_id=booking.buyer_id,
                seller_id=booking.seller_id,
                status=booking.status.value,
                total_pence=booking.total_pence,
                commission_pence=booking.commission_pence,
                first_decision_due_at=dispute.first_decision_due_at,
                under_value_threshold=booking.total_pence
                <= DISPUTE_SLA_THRESHOLD_PENCE,
                created_at=booking.created_at,
                updated_at=booking.updated_at,
            )
            for booking, dispute in pairs
        ]
    )


@router.get(
    "/report",
    response_model=AdminReportResponse,
    summary="Admin platform report",
    description=(
        "Users/sellers/buyers/listings/bookings counts, GMV (booking value "
        "before commission), revenue (commission + featured + subscriptions), "
        "and commission earned."
    ),
)
async def admin_report(
    user: CurrentUser = Depends(require_role(UserRole.ADMIN)),
) -> AdminReportResponse:
    del user
    data = analytics_service.admin_report()
    return AdminReportResponse(**data)
