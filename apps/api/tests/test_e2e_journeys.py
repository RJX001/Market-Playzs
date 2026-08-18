"""End-to-end journey tests — booking state machine + refund calculator.

Skips gracefully when a collaborator module has not landed yet.
"""

from __future__ import annotations

import inspect
from datetime import date, timedelta
from typing import Any, Callable

import pytest

from app.domain_enums import BookingStatus
from app.repositories.memory_store import store


def _load_booking_service():
    try:
        from app.services import booking_service
    except ImportError:
        pytest.skip("booking_service not present")
    return booking_service


def _load_refund_calculator() -> Callable[..., int]:
    """Resolve the refund helper if it exists; otherwise skip."""
    candidates: list[tuple[str, str]] = [
        ("app.services.refund_policy", "calculate_refund_pence"),
        ("app.services.refund_calculator", "calculate_refund_pence"),
        ("app.services.refund_calculator", "calculate_refund"),
        ("app.services.booking_service", "calculate_refund_pence"),
        ("app.services.booking_service", "calculate_refund"),
    ]
    for module_name, attr in candidates:
        try:
            module = __import__(module_name, fromlist=[attr])
        except ImportError:
            continue
        fn = getattr(module, attr, None)
        if callable(fn):
            return fn
    pytest.skip("refund calculator not present")


def _call_refund(
    fn: Callable[..., Any],
    *,
    days_until_start: int,
    cancelled_by: str,
    total_pence: int,
) -> int:
    kwargs: dict[str, Any] = {}
    params = inspect.signature(fn).parameters
    if "days_until_start" in params:
        kwargs["days_until_start"] = days_until_start
    elif "days" in params:
        kwargs["days"] = days_until_start
    if "start_date" in params:
        kwargs["start_date"] = date.today() + timedelta(days=days_until_start)
    if "cancelled_by" in params:
        kwargs["cancelled_by"] = cancelled_by
    elif "actor" in params:
        kwargs["actor"] = cancelled_by
    if "total_pence" in params:
        kwargs["total_pence"] = total_pence
    elif "amount_pence" in params:
        kwargs["amount_pence"] = total_pence
    result = fn(**kwargs) if kwargs else fn(days_until_start, cancelled_by, total_pence)
    if isinstance(result, tuple):
        result = result[0]
    return int(result)


def test_buyer_journey_book_pay_review_completes() -> None:
    """Buyer: book → pay → live → proof → review → Completed."""
    booking_service = _load_booking_service()

    start = date.today()
    end = start + timedelta(days=1)
    booking, secret = booking_service.create_booking(
        listing_id="listing-seed-1",
        buyer_id="buyer-1",
        start_date=start,
        end_date=end,
    )
    assert secret
    assert booking.status == BookingStatus.PENDING_PAYMENT
    assert booking.stripe_payment_intent_id

    confirmed = booking_service.mark_payment_succeeded(booking.stripe_payment_intent_id)
    assert confirmed.status == BookingStatus.CONFIRMED

    live = booking_service.transition(booking.id, BookingStatus.LIVE)
    assert live.status == BookingStatus.LIVE

    awaiting_proof = booking_service.transition(
        booking.id, BookingStatus.AWAITING_PROOF
    )
    assert awaiting_proof.status == BookingStatus.AWAITING_PROOF

    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    awaiting_review = booking_service.upload_proof(booking.id, listing.seller_id)
    assert awaiting_review.status == BookingStatus.AWAITING_BUYER_REVIEW

    completed, listing_cis = booking_service.submit_review(
        booking_id=booking.id,
        buyer_id="buyer-1",
        rating=5,
        delivery_score=1.0,
        comment="Seed journey review",
    )
    assert completed.status == BookingStatus.COMPLETED
    assert listing_cis is None or isinstance(listing_cis, (int, float))


def test_refund_calculator_policy() -> None:
    """Cancellation policy: >7d 100%, 3–7d 50%, <3d 0%, seller-cancels 100%."""
    fn = _load_refund_calculator()
    total = 10_000

    assert _call_refund(
        fn, days_until_start=10, cancelled_by="buyer", total_pence=total
    ) == total
    assert _call_refund(
        fn, days_until_start=5, cancelled_by="buyer", total_pence=total
    ) == total // 2
    assert _call_refund(
        fn, days_until_start=1, cancelled_by="buyer", total_pence=total
    ) == 0
    assert _call_refund(
        fn, days_until_start=1, cancelled_by="seller", total_pence=total
    ) == total
