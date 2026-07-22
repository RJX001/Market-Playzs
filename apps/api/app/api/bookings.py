"""Bookings API — create + review. No client status PATCH."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.repositories.memory_store import store
from app.schemas.bookings import (
    BookingCreate,
    BookingCreateResponse,
    BookingResponse,
    ReviewCreate,
    ReviewResponse,
)
from app.services import booking_service
from app.services.booking_service import (
    BookingServiceError,
    InvalidTransitionError,
)

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


def _to_response(booking) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        listing_id=booking.listing_id,
        buyer_id=booking.buyer_id,
        seller_id=booking.seller_id,
        status=booking.status,
        start_date=booking.start_date,
        end_date=booking.end_date,
        total_pence=booking.total_pence,
        commission_pence=booking.commission_pence,
        stripe_payment_intent_id=booking.stripe_payment_intent_id,
        stripe_transfer_id=booking.stripe_transfer_id,
        delivery_score=booking.delivery_score,
        rating=booking.rating,
        booking_cis=booking.booking_cis,
        created_at=booking.created_at,
        updated_at=booking.updated_at,
    )


@router.post(
    "",
    response_model=BookingCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_booking(
    body: BookingCreate,
    user: CurrentUser = Depends(require_role(UserRole.BUYER)),
) -> BookingCreateResponse:
    """Create booking, lock availability, PaymentIntent → booking_id + client_secret."""
    try:
        booking, client_secret = booking_service.create_booking(
            listing_id=body.listing_id,
            buyer_id=user.id,
            start_date=body.start_date,
            end_date=body.end_date,
        )
    except BookingServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return BookingCreateResponse(
        booking_id=booking.id,
        client_secret=client_secret,
        status=booking.status,
        total_pence=booking.total_pence,
    )


@router.get("/{booking_id}", response_model=BookingResponse)
async def get_booking(
    booking_id: str,
    user: CurrentUser = Depends(
        require_role(UserRole.BUYER, UserRole.SELLER, UserRole.ADMIN)
    ),
) -> BookingResponse:
    booking = store.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if user.role == UserRole.BUYER and booking.buyer_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    if user.role == UserRole.SELLER and booking.seller_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    return _to_response(booking)


@router.post("/{booking_id}/review", response_model=ReviewResponse)
async def submit_review(
    booking_id: str,
    body: ReviewCreate,
    user: CurrentUser = Depends(require_role(UserRole.BUYER)),
) -> ReviewResponse:
    """Buyer rating submission → Completed + CIS recalculation."""
    try:
        booking, listing_cis = booking_service.submit_review(
            booking_id=booking_id,
            buyer_id=user.id,
            rating=body.rating,
            delivery_score=body.delivery_score,
            comment=body.comment,
        )
    except (BookingServiceError, InvalidTransitionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return ReviewResponse(
        booking_id=booking.id,
        listing_id=booking.listing_id,
        rating=body.rating,
        delivery_score=body.delivery_score,
        listing_cis=listing_cis,
        status=booking.status,
    )


@router.post("/{booking_id}/proof", response_model=BookingResponse)
async def upload_proof(
    booking_id: str,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> BookingResponse:
    """Seller proof upload: Awaiting_Proof → Awaiting_Buyer_Review."""
    try:
        booking = booking_service.upload_proof(booking_id, user.id)
    except (BookingServiceError, InvalidTransitionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(booking)


@router.post("/{booking_id}/report-issue", response_model=BookingResponse)
async def report_issue(
    booking_id: str,
    user: CurrentUser = Depends(require_role(UserRole.BUYER)),
) -> BookingResponse:
    """Buyer report: Awaiting_Buyer_Review → Disputed."""
    try:
        booking = booking_service.report_issue(booking_id, user.id)
    except (BookingServiceError, InvalidTransitionError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(booking)
