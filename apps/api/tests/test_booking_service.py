"""Booking state machine tests — Section 5.2 only."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest

from app.domain_enums import BookingStatus, UserRole
from app.repositories.memory_store import BookingRecord, new_id, store
from app.services import booking_service
from app.services.booking_service import BookingServiceError, InvalidTransitionError
from app.services.refund_policy import (
    CancelActor,
    calculate_refund_pence,
    refund_percent,
)


def _insert_booking(
    status: BookingStatus,
    *,
    start: date | None = None,
    end: date | None = None,
    created_at: datetime | None = None,
    updated_at: datetime | None = None,
    buyer_id: str = "buyer-1",
    total_pence: int = 7500,
) -> BookingRecord:
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    start = start or date.today()
    end = end or (start + timedelta(days=2))
    kwargs: dict = dict(
        id=new_id(),
        listing_id=listing.id,
        buyer_id=buyer_id,
        seller_id=listing.seller_id,
        status=status,
        start_date=start,
        end_date=end,
        total_pence=total_pence,
        commission_pence=750,
        stripe_payment_intent_id="pi_test",
        delivery_score=1.0,
        rating=5,
        booking_cis=100.0,
    )
    if created_at is not None:
        kwargs["created_at"] = created_at
    if updated_at is not None:
        kwargs["updated_at"] = updated_at
    booking = BookingRecord(**kwargs)
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


def test_terminal_cancelled_cannot_transition() -> None:
    b = _insert_booking(BookingStatus.CANCELLED)
    with pytest.raises(InvalidTransitionError):
        booking_service.transition(b.id, BookingStatus.CONFIRMED)


def test_terminal_refunded_cannot_transition() -> None:
    b = _insert_booking(BookingStatus.REFUNDED)
    with pytest.raises(InvalidTransitionError):
        booking_service.transition(b.id, BookingStatus.COMPLETED)


def test_admin_flagged_has_no_outbound_transitions() -> None:
    b = _insert_booking(BookingStatus.ADMIN_FLAGGED)
    for target in BookingStatus:
        if target is BookingStatus.ADMIN_FLAGGED:
            continue
        with pytest.raises(InvalidTransitionError):
            booking_service.transition(b.id, target)


def test_confirmed_to_cancelled_allowed() -> None:
    b = _insert_booking(BookingStatus.CONFIRMED)
    updated = booking_service.transition(b.id, BookingStatus.CANCELLED)
    assert updated.status == BookingStatus.CANCELLED


def test_live_to_disputed_allowed() -> None:
    b = _insert_booking(BookingStatus.LIVE)
    updated = booking_service.transition(b.id, BookingStatus.DISPUTED)
    assert updated.status == BookingStatus.DISPUTED


def test_disputed_to_refunded_allowed() -> None:
    b = _insert_booking(BookingStatus.DISPUTED)
    updated = booking_service.transition(b.id, BookingStatus.REFUNDED)
    assert updated.status == BookingStatus.REFUNDED


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


def test_release_abandoned_pending_payment_after_15_minutes() -> None:
    start = date.today()
    end = start + timedelta(days=1)
    booking, _ = booking_service.create_booking(
        listing_id="listing-seed-1",
        buyer_id="buyer-1",
        start_date=start,
        end_date=end,
    )
    stale = datetime.now(timezone.utc) - timedelta(minutes=16)
    store.update_booking(booking.id, created_at=stale)

    released = booking_service.release_abandoned_pending_payment()
    assert [r.id for r in released] == [booking.id]
    updated = store.get_booking(booking.id)
    assert updated is not None
    assert updated.status == BookingStatus.CANCELLED
    unlocked = store.get_availability_for_range("listing-seed-1", start, end)
    assert all(not row.is_locked for row in unlocked)


def test_release_abandoned_skips_fresh_pending_payment() -> None:
    start = date.today()
    end = start + timedelta(days=1)
    booking, _ = booking_service.create_booking(
        listing_id="listing-seed-1",
        buyer_id="buyer-1",
        start_date=start,
        end_date=end,
    )
    released = booking_service.release_abandoned_pending_payment()
    assert released == []
    updated = store.get_booking(booking.id)
    assert updated is not None
    assert updated.status == BookingStatus.PENDING_PAYMENT


def test_run_confirmed_to_live_on_start_date() -> None:
    today = date.today()
    b = _insert_booking(
        BookingStatus.CONFIRMED, start=today, end=today + timedelta(days=2)
    )
    moved = booking_service.run_confirmed_to_live(today=today)
    assert [m.id for m in moved] == [b.id]
    updated = store.get_booking(b.id)
    assert updated is not None
    assert updated.status == BookingStatus.LIVE


def test_run_confirmed_to_live_skips_future_start() -> None:
    today = date.today()
    b = _insert_booking(
        BookingStatus.CONFIRMED,
        start=today + timedelta(days=3),
        end=today + timedelta(days=5),
    )
    moved = booking_service.run_confirmed_to_live(today=today)
    assert moved == []
    updated = store.get_booking(b.id)
    assert updated is not None
    assert updated.status == BookingStatus.CONFIRMED


def test_run_live_to_awaiting_proof_after_end_date() -> None:
    today = date.today()
    b = _insert_booking(
        BookingStatus.LIVE,
        start=today - timedelta(days=3),
        end=today - timedelta(days=1),
    )
    moved = booking_service.run_live_to_awaiting_proof(today=today)
    assert [m.id for m in moved] == [b.id]
    updated = store.get_booking(b.id)
    assert updated is not None
    assert updated.status == BookingStatus.AWAITING_PROOF


def test_run_live_to_awaiting_proof_keeps_campaign_on_end_date() -> None:
    today = date.today()
    b = _insert_booking(BookingStatus.LIVE, start=today, end=today)
    moved = booking_service.run_live_to_awaiting_proof(today=today)
    assert moved == []
    updated = store.get_booking(b.id)
    assert updated is not None
    assert updated.status == BookingStatus.LIVE


def test_flag_stale_awaiting_proof_after_48_hours() -> None:
    now = datetime.now(timezone.utc)
    b = _insert_booking(
        BookingStatus.AWAITING_PROOF,
        updated_at=now - timedelta(hours=49),
    )
    flagged = booking_service.flag_stale_awaiting_proof(now=now)
    assert [f.id for f in flagged] == [b.id]
    updated = store.get_booking(b.id)
    assert updated is not None
    assert updated.status == BookingStatus.ADMIN_FLAGGED


def test_flag_stale_awaiting_proof_skips_fresh() -> None:
    now = datetime.now(timezone.utc)
    b = _insert_booking(
        BookingStatus.AWAITING_PROOF, updated_at=now - timedelta(hours=12)
    )
    flagged = booking_service.flag_stale_awaiting_proof(now=now)
    assert flagged == []
    updated = store.get_booking(b.id)
    assert updated is not None
    assert updated.status == BookingStatus.AWAITING_PROOF


def test_auto_approve_stale_reviews_after_72_hours() -> None:
    now = datetime.now(timezone.utc)
    b = _insert_booking(
        BookingStatus.AWAITING_BUYER_REVIEW,
        updated_at=now - timedelta(hours=73),
    )
    completed = booking_service.auto_approve_stale_reviews(now=now)
    assert [c.id for c in completed] == [b.id]
    updated = store.get_booking(b.id)
    assert updated is not None
    assert updated.status == BookingStatus.COMPLETED
    assert updated.rating == 3
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    assert listing.cis_score is not None


def test_run_daily_transitions_counts() -> None:
    today = date.today()
    now = datetime.now(timezone.utc)
    live_ready = _insert_booking(
        BookingStatus.CONFIRMED, start=today, end=today + timedelta(days=2)
    )
    proof_ready = _insert_booking(
        BookingStatus.LIVE,
        start=today - timedelta(days=2),
        end=today - timedelta(days=1),
    )
    counts = booking_service.run_daily_transitions(today=today, now=now)
    assert counts["confirmed_to_live"] == 1
    assert counts["live_to_awaiting_proof"] == 1
    live_updated = store.get_booking(live_ready.id)
    proof_updated = store.get_booking(proof_ready.id)
    assert live_updated is not None
    assert proof_updated is not None
    assert live_updated.status == BookingStatus.LIVE
    assert proof_updated.status == BookingStatus.AWAITING_PROOF


@pytest.mark.parametrize(
    ("days_until", "cancelled_by", "expected_percent"),
    [
        (8, "buyer", 100),
        (7, "buyer", 50),
        (3, "buyer", 50),
        (2, "buyer", 0),
        (0, "buyer", 0),
        (1, "seller", 100),
        (2, "seller", 100),
        (10, "seller", 100),
    ],
)
def test_refund_percent_policy(
    days_until: int, cancelled_by: CancelActor, expected_percent: int
) -> None:
    today = date(2026, 8, 18)
    start = today + timedelta(days=days_until)
    percent = refund_percent(
        cancelled_by=cancelled_by,
        start_date=start,
        today=today,
    )
    assert percent == expected_percent


def test_calculate_refund_pence_half_of_odd_total() -> None:
    today = date(2026, 8, 18)
    start = today + timedelta(days=5)  # 3–7 → 50%
    pence, percent = calculate_refund_pence(
        total_pence=7501,
        cancelled_by="buyer",
        start_date=start,
        today=today,
    )
    assert percent == 50
    assert pence == 3750  # round(7501 * 0.5)


def test_buyer_cancel_confirmed_full_refund() -> None:
    today = date.today()
    b = _insert_booking(
        BookingStatus.CONFIRMED,
        start=today + timedelta(days=10),
        end=today + timedelta(days=12),
    )
    result = booking_service.cancel_booking(
        booking_id=b.id,
        actor_id="buyer-1",
        actor_role=UserRole.BUYER,
        today=today,
    )
    assert result.booking.status == BookingStatus.CANCELLED
    assert result.refund_percent == 100
    assert result.refund_pence == b.total_pence


def test_buyer_cancel_confirmed_half_refund() -> None:
    today = date.today()
    b = _insert_booking(
        BookingStatus.CONFIRMED,
        start=today + timedelta(days=5),
        end=today + timedelta(days=7),
    )
    result = booking_service.cancel_booking(
        booking_id=b.id,
        actor_id="buyer-1",
        actor_role=UserRole.BUYER,
        today=today,
    )
    assert result.booking.status == BookingStatus.CANCELLED
    assert result.refund_percent == 50
    assert result.refund_pence == 3750


def test_buyer_cancel_half_refund_calls_stripe(monkeypatch: pytest.MonkeyPatch) -> None:
    today = date.today()
    refund = MagicMock(return_value="re_mock_partial")
    monkeypatch.setattr(
        "app.services.booking_service.stripe_service.refund_payment",
        refund,
    )
    b = _insert_booking(
        BookingStatus.CONFIRMED,
        start=today + timedelta(days=5),
        end=today + timedelta(days=7),
    )
    booking_service.cancel_booking(
        booking_id=b.id,
        actor_id="buyer-1",
        actor_role=UserRole.BUYER,
        today=today,
    )
    refund.assert_called_once()
    assert refund.call_args.kwargs["amount_pence"] == 3750


def test_buyer_cancel_zero_refund_skips_stripe(monkeypatch: pytest.MonkeyPatch) -> None:
    today = date.today()
    refund = MagicMock()
    monkeypatch.setattr(
        "app.services.booking_service.stripe_service.refund_payment",
        refund,
    )
    b = _insert_booking(
        BookingStatus.CONFIRMED,
        start=today + timedelta(days=2),
        end=today + timedelta(days=4),
    )
    booking_service.cancel_booking(
        booking_id=b.id,
        actor_id="buyer-1",
        actor_role=UserRole.BUYER,
        today=today,
    )
    refund.assert_not_called()


def test_buyer_cancel_confirmed_no_refund() -> None:
    today = date.today()
    b = _insert_booking(
        BookingStatus.CONFIRMED,
        start=today + timedelta(days=2),
        end=today + timedelta(days=4),
    )
    result = booking_service.cancel_booking(
        booking_id=b.id,
        actor_id="buyer-1",
        actor_role=UserRole.BUYER,
        today=today,
    )
    assert result.booking.status == BookingStatus.CANCELLED
    assert result.refund_percent == 0
    assert result.refund_pence == 0


def test_seller_cancel_always_full_refund() -> None:
    today = date.today()
    b = _insert_booking(
        BookingStatus.CONFIRMED,
        start=today + timedelta(days=1),
        end=today + timedelta(days=3),
    )
    result = booking_service.cancel_booking(
        booking_id=b.id,
        actor_id="seller-seed-1",
        actor_role=UserRole.SELLER,
        today=today,
    )
    assert result.booking.status == BookingStatus.CANCELLED
    assert result.refund_percent == 100
    assert result.refund_pence == b.total_pence


def test_cancel_pending_payment_has_zero_refund() -> None:
    b = _insert_booking(
        BookingStatus.PENDING_PAYMENT,
        start=date.today() + timedelta(days=10),
    )
    result = booking_service.cancel_booking(
        booking_id=b.id,
        actor_id="buyer-1",
        actor_role=UserRole.BUYER,
    )
    assert result.booking.status == BookingStatus.CANCELLED
    assert result.refund_pence == 0
    assert result.refund_percent == 0


def test_cancel_rejects_non_owner_buyer() -> None:
    b = _insert_booking(BookingStatus.CONFIRMED, start=date.today() + timedelta(days=10))
    with pytest.raises(BookingServiceError, match="buyer"):
        booking_service.cancel_booking(
            booking_id=b.id,
            actor_id="other-buyer",
            actor_role=UserRole.BUYER,
        )


def test_cancel_rejects_after_start() -> None:
    today = date.today()
    b = _insert_booking(BookingStatus.CONFIRMED, start=today, end=today + timedelta(days=1))
    with pytest.raises(BookingServiceError, match="campaign start"):
        booking_service.cancel_booking(
            booking_id=b.id,
            actor_id="buyer-1",
            actor_role=UserRole.BUYER,
            today=today,
        )


def test_cancel_rejects_live_status() -> None:
    b = _insert_booking(BookingStatus.LIVE, start=date.today() + timedelta(days=10))
    with pytest.raises(BookingServiceError, match="Cannot cancel"):
        booking_service.cancel_booking(
            booking_id=b.id,
            actor_id="buyer-1",
            actor_role=UserRole.BUYER,
        )


def test_cancel_unlocks_availability() -> None:
    start = date.today() + timedelta(days=10)
    end = start + timedelta(days=1)
    store.ensure_availability_window("listing-seed-1", start, end)
    booking, _ = booking_service.create_booking(
        listing_id="listing-seed-1",
        buyer_id="buyer-1",
        start_date=start,
        end_date=end,
    )
    booking_service.transition(booking.id, BookingStatus.CONFIRMED)
    result = booking_service.cancel_booking(
        booking_id=booking.id,
        actor_id="buyer-1",
        actor_role=UserRole.BUYER,
        today=date.today(),
    )
    assert result.booking.status == BookingStatus.CANCELLED
    unlocked = store.get_availability_for_range("listing-seed-1", start, end)
    assert all(not row.is_locked for row in unlocked)
