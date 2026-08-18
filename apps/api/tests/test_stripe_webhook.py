"""Stripe webhook signature + payments route tests."""

from __future__ import annotations

import json
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import CurrentUser, get_current_user
from app.domain_enums import BookingStatus, Category, ListingStatus, UserRole
from app.main import app
from app.repositories.memory_store import BookingRecord, ListingRecord, new_id, store
from app.services import booking_service, stripe_service
from app.services.stripe_service import (
    InvalidStripeSignatureError,
    StripeServiceError,
    construct_webhook_event,
    transfer_on_completed,
)


def _client() -> TestClient:
    return TestClient(app)


def _signed_webhook(payload: dict) -> object:
    client = _client()
    return client.post(
        "/api/payments/webhook",
        content=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "t=1,v1=mock",
        },
    )


def test_missing_signature_rejected() -> None:
    with pytest.raises(InvalidStripeSignatureError):
        construct_webhook_event(b"{}", None)


def test_invalid_signature_rejected() -> None:
    with pytest.raises(InvalidStripeSignatureError):
        construct_webhook_event(b'{"type":"x"}', "invalid")


def test_webhook_route_returns_400_on_bad_signature() -> None:
    client = _client()
    response = client.post(
        "/api/payments/webhook",
        content=json.dumps({"type": "payment_intent.succeeded"}),
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "invalid",
        },
    )
    assert response.status_code == 400


def test_webhook_route_returns_400_when_unsigned() -> None:
    client = _client()
    response = client.post(
        "/api/payments/webhook",
        content=json.dumps({"type": "payment_intent.succeeded"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400


def test_webhook_route_accepts_mock_valid_signature() -> None:
    payload = {
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_unknown"}},
    }
    response = _signed_webhook(payload)
    assert response.status_code == 200


def test_webhook_payment_failed_cancels_and_releases_availability() -> None:
    start = date.today()
    end = start + timedelta(days=1)
    booking, _secret = booking_service.create_booking(
        listing_id="listing-seed-1",
        buyer_id="buyer-1",
        start_date=start,
        end_date=end,
    )
    assert booking.status == BookingStatus.PENDING_PAYMENT
    locked = store.get_availability_for_range("listing-seed-1", start, end)
    assert locked
    assert all(row.is_locked for row in locked)

    response = _signed_webhook(
        {
            "type": "payment_intent.payment_failed",
            "data": {"object": {"id": booking.stripe_payment_intent_id}},
        }
    )
    assert response.status_code == 200

    updated = store.get_booking(booking.id)
    assert updated is not None
    assert updated.status == BookingStatus.CANCELLED
    released = store.get_availability_for_range("listing-seed-1", start, end)
    assert all(not row.is_locked for row in released)
    assert all(row.booking_id is None for row in released)


def test_webhook_payment_succeeded_confirms_without_transfer() -> None:
    start = date.today() + timedelta(days=2)
    end = start
    booking, _secret = booking_service.create_booking(
        listing_id="listing-seed-1",
        buyer_id="buyer-1",
        start_date=start,
        end_date=end,
    )
    response = _signed_webhook(
        {
            "type": "payment_intent.succeeded",
            "data": {"object": {"id": booking.stripe_payment_intent_id}},
        }
    )
    assert response.status_code == 200
    updated = store.get_booking(booking.id)
    assert updated is not None
    assert updated.status == BookingStatus.CONFIRMED
    assert updated.stripe_transfer_id is None


def test_webhook_transfer_paid_records_transfer_id() -> None:
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    booking = store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id=listing.id,
            buyer_id="buyer-1",
            seller_id=listing.seller_id,
            status=BookingStatus.COMPLETED,
            start_date=date.today(),
            end_date=date.today(),
            total_pence=7500,
            commission_pence=750,
            stripe_payment_intent_id="pi_paid",
        )
    )
    response = _signed_webhook(
        {
            "type": "transfer.paid",
            "data": {
                "object": {
                    "id": "tr_live_123",
                    "metadata": {"booking_id": booking.id},
                }
            },
        }
    )
    assert response.status_code == 200
    updated = store.get_booking(booking.id)
    assert updated is not None
    assert updated.stripe_transfer_id == "tr_live_123"


def test_transfer_on_completed_rejected_before_completed() -> None:
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    booking = store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id=listing.id,
            buyer_id="buyer-1",
            seller_id=listing.seller_id,
            status=BookingStatus.CONFIRMED,
            start_date=date.today(),
            end_date=date.today(),
            total_pence=7500,
            commission_pence=750,
            stripe_payment_intent_id="pi_hold",
        )
    )
    with pytest.raises(StripeServiceError, match="Completed"):
        transfer_on_completed(booking)


def test_transfer_on_completed_when_completed() -> None:
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    booking = store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id=listing.id,
            buyer_id="buyer-1",
            seller_id=listing.seller_id,
            status=BookingStatus.COMPLETED,
            start_date=date.today(),
            end_date=date.today(),
            total_pence=7500,
            commission_pence=750,
            stripe_payment_intent_id="pi_done",
        )
    )
    transfer_id = transfer_on_completed(booking)
    assert transfer_id
    assert transfer_id.startswith("tr_mock_")


def test_payouts_requires_auth() -> None:
    client = _client()
    response = client.get("/api/payments/payouts")
    assert response.status_code == 401


def test_payouts_seller_own_listings_only() -> None:
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    own = store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id=listing.id,
            buyer_id="buyer-1",
            seller_id=listing.seller_id,
            status=BookingStatus.COMPLETED,
            start_date=date.today(),
            end_date=date.today(),
            total_pence=10000,
            commission_pence=1000,
            stripe_payment_intent_id="pi_own",
            stripe_transfer_id="tr_own",
        )
    )
    other_listing = store.create_listing(
        ListingRecord(
            id="listing-other-seller",
            seller_id="other-seller",
            title="Other",
            description="Not ours",
            category=Category.CAFE,
            status=ListingStatus.PUBLISHED,
            price_per_day_pence=1000,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/x.webp"],
        )
    )
    store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id=other_listing.id,
            buyer_id="buyer-2",
            seller_id="other-seller",
            status=BookingStatus.COMPLETED,
            start_date=date.today(),
            end_date=date.today(),
            total_pence=5000,
            commission_pence=500,
            stripe_payment_intent_id="pi_other",
            stripe_transfer_id="tr_other",
        )
    )

    async def _seller() -> CurrentUser:
        return CurrentUser(
            id=listing.seller_id, role=UserRole.SELLER, email="seller@example.com"
        )

    app.dependency_overrides[get_current_user] = _seller
    try:
        client = _client()
        response = client.get("/api/payments/payouts")
        assert response.status_code == 200
        items = response.json()["items"]
        transfer_ids = {row["stripe_transfer_id"] for row in items}
        assert "tr_own" in transfer_ids
        assert "tr_other" not in transfer_ids
        mine = next(row for row in items if row["booking_id"] == own.id)
        assert mine["amount_pence"] == 9000
        assert mine["listing_id"] == listing.id
    finally:
        app.dependency_overrides.clear()


def test_openapi_payments_summaries() -> None:
    client = _client()
    spec = client.get("/openapi.json").json()
    paths = spec["paths"]
    assert (
        paths["/api/payments/webhook"]["post"]["summary"] == "Stripe webhook"
    )
    assert (
        paths["/api/payments/connect/account-link"]["post"]["summary"]
        == "Create Stripe Connect onboarding link"
    )
    assert (
        paths["/api/payments/payouts"]["get"]["summary"]
        == "List seller payout history"
    )
