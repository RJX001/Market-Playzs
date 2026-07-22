"""Booking state machine tests — Section 5.2 only."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.domain_enums import BookingStatus
from app.repositories.memory_store import BookingRecord, new_id, store
from app.services import booking_service
from app.services.booking_service import InvalidTransitionError


def _insert_booking(status: BookingStatus) -> BookingRecord:
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    start = date.today()
    end = start + timedelta(days=2)
    booking = BookingRecord(
        id=new_id(),
        listing_id=listing.id,
        buyer_id="buyer-1",
        seller_id=listing.seller_id,
        status=status,
        start_date=start,
        end_date=end,
        total_pence=7500,
        commission_pence=750,
        stripe_payment_intent_id="pi_test",
        delivery_score=1.0,
        rating=5,
        booking_cis=100.0,
    )
    return store.create_booking(booking)


def test_valid_pending_to_confirmed() -> None:
    b = _insert_booking(BookingStatus.PENDING_PAYMENT)
    updated = booking_service.transition(b.id, BookingStatus.CONFIRMED)
    assert updated.status == BookingStatus.CONFIRMED


def test_invalid_pending_to_live_rejected() -> None:
    b = _insert_booking(BookingStatus.PENDING_PAYMENT)
    with pytest.raises(InvalidTransitionError):
        booking_service.transition(b.id, BookingStatus.LIVE)


def test_terminal_completed_cannot_transition() -> None:
    b = _insert_booking(BookingStatus.COMPLETED)
    with pytest.raises(InvalidTransitionError):
        booking_service.transition(b.id, BookingStatus.REFUNDED)


def test_create_booking_locks_and_returns_client_secret() -> None:
    start = date.today()
    end = start + timedelta(days=1)
    booking, secret = booking_service.create_booking(
        listing_id="listing-seed-1",
        buyer_id="buyer-1",
        start_date=start,
        end_date=end,
    )
    assert booking.status == BookingStatus.PENDING_PAYMENT
    assert booking.total_pence == 5000  # 2500 * 2 days
    assert secret
    assert booking.stripe_payment_intent_id
    locked = store.get_availability_for_range("listing-seed-1", start, end)
    assert all(row.is_locked for row in locked)
