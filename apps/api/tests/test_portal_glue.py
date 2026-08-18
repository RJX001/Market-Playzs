"""Glue tests: booking list, seller inventory, admin moderation aliases."""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.api.deps import CurrentUser, get_current_user
from app.domain_enums import BookingStatus, ListingStatus, UserRole
from app.main import app
from app.repositories.memory_store import BookingRecord, ListingRecord, new_id, store
from app.services import listing_service


BUYER = CurrentUser(id="buyer-1", role=UserRole.BUYER, email="buyer@test.com")
SELLER = CurrentUser(id="seller-seed-1", role=UserRole.SELLER, email="seller@test.com")
ADMIN = CurrentUser(id="admin-1", role=UserRole.ADMIN, email="admin@test.com")
OTHER_BUYER = CurrentUser(id="buyer-2", role=UserRole.BUYER, email="buyer2@test.com")


@pytest.fixture
def client() -> TestClient:
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _auth(user: CurrentUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


def test_list_bookings_buyer_own_only(client: TestClient) -> None:
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    mine = store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id=listing.id,
            buyer_id=BUYER.id,
            seller_id=listing.seller_id,
            status=BookingStatus.CONFIRMED,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            total_pence=5000,
            commission_pence=500,
        )
    )
    store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id=listing.id,
            buyer_id=OTHER_BUYER.id,
            seller_id=listing.seller_id,
            status=BookingStatus.CONFIRMED,
            start_date=date.today() + timedelta(days=10),
            end_date=date.today() + timedelta(days=12),
            total_pence=4000,
            commission_pence=400,
        )
    )
    _auth(BUYER)
    response = client.get("/api/bookings")
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["items"]}
    assert mine.id in ids
    assert all(
        row["buyer_id"] == BUYER.id for row in response.json()["items"]
    )


def test_list_bookings_seller_own_only(client: TestClient) -> None:
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    own = store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id=listing.id,
            buyer_id=BUYER.id,
            seller_id=listing.seller_id,
            status=BookingStatus.LIVE,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=1),
            total_pence=7500,
            commission_pence=750,
        )
    )
    _auth(SELLER)
    response = client.get("/api/bookings")
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["items"]}
    assert own.id in ids
    assert all(
        row["seller_id"] == listing.seller_id for row in response.json()["items"]
    )


def test_list_my_listings_includes_drafts(client: TestClient) -> None:
    draft = listing_service.create_listing_draft(
        SELLER.id,
        {
            "title": "Glue draft",
            "description": "Owner can see drafts",
            "category": store.get_listing("listing-seed-1").category,
            "price_per_day_pence": 1000,
            "lat": 51.5,
            "lng": -0.1,
            "images": [],
        },
    )
    _auth(SELLER)
    response = client.get("/api/listings/mine")
    assert response.status_code == 200
    ids = {row["id"] for row in response.json()["items"]}
    assert draft.id in ids
    statuses = {row["status"] for row in response.json()["items"]}
    assert ListingStatus.DRAFT.value in statuses


def test_mine_is_not_treated_as_listing_id(client: TestClient) -> None:
    response = client.get("/api/listings/mine")
    assert response.status_code == 401


def test_admin_moderation_alias(client: TestClient) -> None:
    _auth(ADMIN)
    canonical = client.get("/api/admin/moderation/listings")
    alias = client.get("/api/admin/moderation")
    assert canonical.status_code == 200
    assert alias.status_code == 200
    assert canonical.json()["items"] == alias.json()["items"]
