"""Booking state machine — only Section 5.2 transitions are allowed.

Clients never PATCH status; transitions are invoked by webhooks, cron,
domain actions (review, proof upload), or explicit admin overrides.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from app.domain_enums import (
    DELIVERY_SCORES,
    TERMINAL_BOOKING_STATUSES,
    VALID_TRANSITIONS,
    BookingStatus,
    ListingStatus,
    UserRole,
)
from app.repositories.memory_store import (
    BookingRecord,
    ReviewRecord,
    new_id,
    store,
)
from app.services import cis_service, notification_service, stripe_service
from app.services.refund_policy import calculate_refund_pence

# Default platform commission rate (10%) — TODO: make configurable per admin
DEFAULT_COMMISSION_RATE = 0.10

PENDING_PAYMENT_TTL = timedelta(minutes=15)
PROOF_TIMEOUT = timedelta(hours=48)
REVIEW_AUTO_APPROVE = timedelta(hours=72)
AUTO_APPROVE_RATING = 3
# Proof is already uploaded by the time the booking is Awaiting_Buyer_Review.
AUTO_APPROVE_DELIVERY_SCORE = 1.0


@dataclass(frozen=True)
class CancelResult:
    booking: BookingRecord
    refund_pence: int
    refund_percent: int


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _list_all_bookings() -> list[BookingRecord]:
    return [
        rec
        for bid in list(store.bookings)
        if (rec := store.get_booking(bid)) is not None
    ]


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


def release_abandoned_pending_payment(
    *, now: datetime | None = None
) -> list[BookingRecord]:
    """Cancel Pending_Payment bookings older than 15 minutes and unlock dates."""
    now = now or _utcnow()
    released: list[BookingRecord] = []
    for booking in _list_all_bookings():
        if booking.status != BookingStatus.PENDING_PAYMENT:
            continue
        age = now - _as_utc(booking.created_at)
        if age < PENDING_PAYMENT_TTL:
            continue
        released.append(
            transition(
                booking.id,
                BookingStatus.CANCELLED,
                actor="cron:abandonment",
            )
        )
    return released


def run_confirmed_to_live(*, today: date | None = None) -> list[BookingRecord]:
    """Confirmed → Live when campaign start_date is reached (daily cron 00:01)."""
    today = today or date.today()
    moved: list[BookingRecord] = []
    for booking in _list_all_bookings():
        if booking.status != BookingStatus.CONFIRMED:
            continue
        if booking.start_date > today:
            continue
        moved.append(
            transition(booking.id, BookingStatus.LIVE, actor="cron:start_date")
        )
    return moved


def run_live_to_awaiting_proof(*, today: date | None = None) -> list[BookingRecord]:
    """Live → Awaiting_Proof after campaign end_date (daily cron)."""
    today = today or date.today()
    moved: list[BookingRecord] = []
    for booking in _list_all_bookings():
        if booking.status != BookingStatus.LIVE:
            continue
        if booking.end_date >= today:
            continue
        moved.append(
            transition(
                booking.id,
                BookingStatus.AWAITING_PROOF,
                actor="cron:end_date",
            )
        )
    return moved


def flag_stale_awaiting_proof(
    *, now: datetime | None = None
) -> list[BookingRecord]:
    """Awaiting_Proof → Admin_Flagged after 48 hours with no proof."""
    now = now or _utcnow()
    flagged: list[BookingRecord] = []
    for booking in _list_all_bookings():
        if booking.status != BookingStatus.AWAITING_PROOF:
            continue
        if now - _as_utc(booking.updated_at) < PROOF_TIMEOUT:
            continue
        flagged.append(
            transition(
                booking.id,
                BookingStatus.ADMIN_FLAGGED,
                actor="cron:proof_timeout",
            )
        )
    return flagged


def auto_approve_stale_reviews(
    *, now: datetime | None = None
) -> list[BookingRecord]:
    """Awaiting_Buyer_Review → Completed after 72 hours; rating defaults to 3."""
    now = now or _utcnow()
    completed: list[BookingRecord] = []
    for booking in _list_all_bookings():
        if booking.status != BookingStatus.AWAITING_BUYER_REVIEW:
            continue
        if now - _as_utc(booking.updated_at) < REVIEW_AUTO_APPROVE:
            continue

        delivery = (
            booking.delivery_score
            if booking.delivery_score in DELIVERY_SCORES
            else AUTO_APPROVE_DELIVERY_SCORE
        )
        rating = AUTO_APPROVE_RATING
        booking_cis = cis_service.compute_booking_cis(delivery, rating)
        store.update_booking(
            booking.id,
            rating=rating,
            delivery_score=delivery,
            booking_cis=booking_cis,
        )
        store.create_review(
            ReviewRecord(
                id=new_id(),
                booking_id=booking.id,
                listing_id=booking.listing_id,
                buyer_id=booking.buyer_id,
                rating=rating,
                delivery_score=delivery,
            )
        )
        completed.append(
            transition(
                booking.id,
                BookingStatus.COMPLETED,
                actor="cron:auto-approve",
            )
        )
        cis_service.recalculate_listing_cis(booking.listing_id)
    return completed


def run_daily_transitions(
    *,
    today: date | None = None,
    now: datetime | None = None,
) -> dict[str, int]:
    """Daily cron entrypoint: date-based transitions plus 48h/72h timeouts."""
    today = today or date.today()
    now = now or _utcnow()
    confirmed_to_live = run_confirmed_to_live(today=today)
    live_to_proof = run_live_to_awaiting_proof(today=today)
    proof_flagged = flag_stale_awaiting_proof(now=now)
    auto_approved = auto_approve_stale_reviews(now=now)
    return {
        "confirmed_to_live": len(confirmed_to_live),
        "live_to_awaiting_proof": len(live_to_proof),
        "proof_timeout_flagged": len(proof_flagged),
        "reviews_auto_approved": len(auto_approved),
    }


def cancel_booking(
    *,
    booking_id: str,
    actor_id: str,
    actor_role: UserRole,
    today: date | None = None,
) -> CancelResult:
    """
    Buyer or seller cancels pre-start.

    Pending_Payment → Cancelled (no Stripe refund; payment never succeeded).
    Confirmed → Cancelled with refund per ``refund_policy``. Any positive
    refund (100% or 50%) calls ``stripe_service.refund_payment`` with
    ``amount_pence``.
    """
    today = today or date.today()
    booking = store.get_booking(booking_id)
    if not booking:
        raise BookingServiceError("Booking not found")

    if actor_role == UserRole.BUYER:
        if booking.buyer_id != actor_id:
            raise BookingServiceError(
                "Only the booking buyer may cancel this booking"
            )
        cancelled_by = "buyer"
    elif actor_role == UserRole.SELLER:
        if booking.seller_id != actor_id:
            raise BookingServiceError(
                "Only the listing seller may cancel this booking"
            )
        cancelled_by = "seller"
    else:
        raise BookingServiceError("Only the buyer or seller may cancel a booking")

    if booking.status not in {
        BookingStatus.PENDING_PAYMENT,
        BookingStatus.CONFIRMED,
    }:
        raise BookingServiceError(
            f"Cannot cancel booking in status {booking.status.value}"
        )

    if (
        booking.status == BookingStatus.CONFIRMED
        and booking.start_date <= today
    ):
        raise BookingServiceError("Cannot cancel after campaign start")

    refund_pence, percent = calculate_refund_pence(
        total_pence=booking.total_pence,
        cancelled_by=cancelled_by,
        start_date=booking.start_date,
        today=today,
    )
    if booking.status == BookingStatus.PENDING_PAYMENT:
        refund_pence, percent = 0, 0

    paid = booking.status == BookingStatus.CONFIRMED
    if paid and refund_pence > 0 and booking.stripe_payment_intent_id:
        stripe_service.refund_payment(booking, amount_pence=refund_pence)

    updated = transition(
        booking_id,
        BookingStatus.CANCELLED,
        actor=f"{actor_role.value}:{actor_id}",
    )
    return CancelResult(
        booking=updated,
        refund_pence=refund_pence,
        refund_percent=percent,
    )
