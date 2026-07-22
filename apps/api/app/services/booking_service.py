"""Booking state machine — only Section 5.2 transitions are allowed.

Clients never PATCH status; transitions are invoked by webhooks, cron,
domain actions (review, proof upload), or explicit admin overrides.
"""

from __future__ import annotations

from datetime import date

from app.domain_enums import (
    DELIVERY_SCORES,
    TERMINAL_BOOKING_STATUSES,
    VALID_TRANSITIONS,
    BookingStatus,
    ListingStatus,
)
from app.repositories.memory_store import (
    BookingRecord,
    ReviewRecord,
    new_id,
    store,
)
from app.services import cis_service, notification_service, stripe_service

# Default platform commission rate (10%) — TODO: make configurable per admin
DEFAULT_COMMISSION_RATE = 0.10


class InvalidTransitionError(ValueError):
    """Raised when a booking status transition is not in Section 5.2."""


class BookingServiceError(ValueError):
    """Domain validation error for booking operations."""


def assert_valid_transition(
    current: BookingStatus, new_status: BookingStatus
) -> None:
    if current in TERMINAL_BOOKING_STATUSES:
        raise InvalidTransitionError(
            f"Terminal status {current.value} cannot transition "
            f"(including admin override tooling)"
        )
    allowed = VALID_TRANSITIONS.get(current, frozenset())
    if new_status not in allowed:
        raise InvalidTransitionError(
            f"Invalid transition {current.value} → {new_status.value}"
        )


def transition(
    booking_id: str,
    new_status: BookingStatus,
    *,
    actor: str = "system",
) -> BookingRecord:
    """Apply a single valid state-machine transition."""
    booking = store.get_booking(booking_id)
    if not booking:
        raise BookingServiceError(f"Booking {booking_id} not found")

    if booking.status == new_status:
        return booking  # idempotent no-op

    assert_valid_transition(booking.status, new_status)

    updated = store.update_booking(booking_id, status=new_status)
    if not updated:
        raise BookingServiceError(f"Booking {booking_id} not found")

    if new_status in {
        BookingStatus.CANCELLED,
        BookingStatus.REFUNDED,
    }:
        store.unlock_availability(booking_id)

    if new_status == BookingStatus.COMPLETED:
        # Hold until Completed — transfer only here (Separate Charges & Transfers)
        transfer_id = stripe_service.transfer_on_completed(updated)
        if transfer_id:
            updated = store.update_booking(
                booking_id, stripe_transfer_id=transfer_id
            ) or updated
        notification_service.notify_booking_completed(updated)

    notification_service.notify_status_change(
        booking_id, updated.status, actor=actor
    )
    return updated


def create_booking(
    *,
    listing_id: str,
    buyer_id: str,
    start_date: date,
    end_date: date,
) -> tuple[BookingRecord, str]:
    """
    Create booking, lock availability, create PaymentIntent.

    Returns (booking, client_secret).
    """
    if end_date < start_date:
        raise BookingServiceError("end_date must be on or after start_date")

    listing = store.get_listing(listing_id)
    if not listing:
        raise BookingServiceError("Listing not found")
    if listing.status != ListingStatus.PUBLISHED:
        raise BookingServiceError("Listing is not published")

    days = (end_date - start_date).days + 1
    total_pence = listing.price_per_day_pence * days
    commission_pence = int(round(total_pence * DEFAULT_COMMISSION_RATE))

    booking_id = new_id()
    try:
        store.lock_availability(listing_id, start_date, end_date, booking_id)
    except ValueError as exc:
        raise BookingServiceError(str(exc)) from exc

    booking = BookingRecord(
        id=booking_id,
        listing_id=listing_id,
        buyer_id=buyer_id,
        seller_id=listing.seller_id,
        status=BookingStatus.PENDING_PAYMENT,
        start_date=start_date,
        end_date=end_date,
        total_pence=total_pence,
        commission_pence=commission_pence,
    )
    store.create_booking(booking)

    try:
        intent = stripe_service.create_payment_intent(booking)
    except Exception:
        store.unlock_availability(booking_id)
        store.update_booking(booking_id, status=BookingStatus.CANCELLED)
        raise

    updated = store.update_booking(
        booking_id, stripe_payment_intent_id=intent["id"]
    )
    assert updated is not None
    notification_service.notify_booking_created(updated)
    return updated, intent["client_secret"]


def submit_review(
    *,
    booking_id: str,
    buyer_id: str,
    rating: int,
    delivery_score: float,
    comment: str | None = None,
) -> tuple[BookingRecord, int | None]:
    """
    Buyer review: Awaiting_Buyer_Review → Completed, then CIS recalc.

    Returns (booking, listing_cis).
    """
    if rating < 1 or rating > 5:
        raise BookingServiceError("rating must be 1–5")
    if delivery_score not in DELIVERY_SCORES:
        raise BookingServiceError("delivery_score must be exactly 0, 0.5, or 1")

    booking = store.get_booking(booking_id)
    if not booking:
        raise BookingServiceError("Booking not found")
    if booking.buyer_id != buyer_id:
        raise BookingServiceError("Only the booking buyer may submit a review")
    if booking.status != BookingStatus.AWAITING_BUYER_REVIEW:
        raise BookingServiceError(
            f"Review requires status Awaiting_Buyer_Review, got {booking.status.value}"
        )

    booking_cis = cis_service.compute_booking_cis(delivery_score, rating)
    store.update_booking(
        booking_id,
        rating=rating,
        delivery_score=delivery_score,
        booking_cis=booking_cis,
    )
    store.create_review(
        ReviewRecord(
            id=new_id(),
            booking_id=booking_id,
            listing_id=booking.listing_id,
            buyer_id=buyer_id,
            rating=rating,
            delivery_score=delivery_score,
            comment=comment,
        )
    )

    completed = transition(
        booking_id, BookingStatus.COMPLETED, actor=f"buyer:{buyer_id}"
    )
    listing_cis = cis_service.recalculate_listing_cis(booking.listing_id)
    return completed, listing_cis


def mark_payment_succeeded(payment_intent_id: str) -> BookingRecord:
    booking = store.get_booking_by_payment_intent(payment_intent_id)
    if not booking:
        raise BookingServiceError("Booking not found for PaymentIntent")
    return transition(
        booking.id, BookingStatus.CONFIRMED, actor="stripe:webhook"
    )


def mark_payment_failed(payment_intent_id: str) -> BookingRecord:
    booking = store.get_booking_by_payment_intent(payment_intent_id)
    if not booking:
        raise BookingServiceError("Booking not found for PaymentIntent")
    return transition(
        booking.id, BookingStatus.CANCELLED, actor="stripe:webhook"
    )


def upload_proof(booking_id: str, seller_id: str) -> BookingRecord:
    booking = store.get_booking(booking_id)
    if not booking:
        raise BookingServiceError("Booking not found")
    if booking.seller_id != seller_id:
        raise BookingServiceError("Only the listing seller may upload proof")
    return transition(
        booking_id,
        BookingStatus.AWAITING_BUYER_REVIEW,
        actor=f"seller:{seller_id}",
    )


def report_issue(booking_id: str, buyer_id: str) -> BookingRecord:
    booking = store.get_booking(booking_id)
    if not booking:
        raise BookingServiceError("Booking not found")
    if booking.buyer_id != buyer_id:
        raise BookingServiceError("Only the booking buyer may report an issue")
    return transition(
        booking_id, BookingStatus.DISPUTED, actor=f"buyer:{buyer_id}"
    )
