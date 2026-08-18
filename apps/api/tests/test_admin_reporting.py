"""B7–B11: verification, analytics, public stats, admin reporting, attribution."""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from app.api.deps import CurrentUser, get_current_user
from app.api.public_stats import clear_cache
from app.domain_enums import BookingStatus, Category, ListingStatus, UserRole
from app.main import app
from app.repositories.memory_store import (
    BookingRecord,
    ListingRecord,
    SellerProfile,
    new_id,
    store,
)

ADMIN = CurrentUser(id="admin-1", role=UserRole.ADMIN, email="admin@test.com")
SELLER = CurrentUser(id="seller-seed-1", role=UserRole.SELLER, email="seller@test.com")
OTHER_SELLER = CurrentUser(id="seller-other", role=UserRole.SELLER, email="other@test.com")
BUYER = CurrentUser(id="buyer-1", role=UserRole.BUYER, email="buyer@test.com")
OTHER_BUYER = CurrentUser(id="buyer-2", role=UserRole.BUYER, email="buyer2@test.com")


@pytest.fixture
def client() -> TestClient:
    clear_cache()
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
    clear_cache()


def _auth(user: CurrentUser) -> None:
    app.dependency_overrides[get_current_user] = lambda: user


def _insert_booking(
    *,
    status: BookingStatus,
    buyer_id: str = "buyer-1",
    seller_id: str = "seller-seed-1",
    listing_id: str = "listing-seed-1",
    total_pence: int = 10_000,
    commission_pence: int = 1_000,
    booking_cis: float | None = 80.0,
    created_at: datetime | None = None,
) -> BookingRecord:
    start = date.today()
    booking = BookingRecord(
        id=new_id(),
        listing_id=listing_id,
        buyer_id=buyer_id,
        seller_id=seller_id,
        status=status,
        start_date=start,
        end_date=start + timedelta(days=2),
        total_pence=total_pence,
        commission_pence=commission_pence,
        stripe_payment_intent_id="pi_test",
        delivery_score=1.0,
        rating=4,
        booking_cis=booking_cis,
    )
    stored = store.create_booking(booking)
    if created_at is not None:
        stored = store.update_booking(stored.id, created_at=created_at) or stored
    return stored


# --- B10 admin reporting / audit / moderation / disputes ---


def test_admin_report_gmv_revenue_commission(client: TestClient) -> None:
    _insert_booking(status=BookingStatus.COMPLETED, total_pence=10_000, commission_pence=1_000)
    _insert_booking(status=BookingStatus.PENDING_PAYMENT, total_pence=5_000, commission_pence=500)
    _auth(ADMIN)
    response = client.get("/api/admin/report")
    assert response.status_code == 200
    body = response.json()
    assert body["listings"] >= 1
    assert body["sellers"] >= 1
    assert body["bookings"] >= 2
    assert body["gmv_pence"] == 10_000
    assert body["commission_pence"] == 1_000
    assert body["revenue_pence"] == 1_000
    assert body["gmv_30d_pence"] == 10_000
    assert "users" in body
    assert "buyers" in body


def test_admin_report_forbidden_for_seller(client: TestClient) -> None:
    _auth(SELLER)
    response = client.get("/api/admin/report")
    assert response.status_code == 403


def test_listing_approve_and_reject_write_audit_logs(client: TestClient) -> None:
    pending = store.create_listing(
        ListingRecord(
            id=new_id(),
            seller_id="seller-seed-1",
            title="Pending cafe",
            description="needs review",
            category=Category.CAFE,
            status=ListingStatus.DRAFT,
            price_per_day_pence=1200,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/a.webp"],
            moderation_status="pending",
        )
    )
    reject_id = new_id()
    store.create_listing(
        ListingRecord(
            id=reject_id,
            seller_id="seller-seed-1",
            title="Reject me",
            description="needs review",
            category=Category.SHOP,
            status=ListingStatus.DRAFT,
            price_per_day_pence=900,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/b.webp"],
            moderation_status="pending",
        )
    )
    _auth(ADMIN)
    queue = client.get("/api/admin/moderation/listings")
    assert queue.status_code == 200
    ids = {item["id"] for item in queue.json()["items"]}
    assert pending.id in ids
    assert reject_id in ids

    approved = client.post(f"/api/admin/listings/{pending.id}/approve")
    assert approved.status_code == 200
    assert approved.json()["status"] == ListingStatus.PUBLISHED.value

    rejected = client.post(
        f"/api/admin/listings/{reject_id}/reject",
        json={"reason": "Incomplete photos"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == ListingStatus.SUSPENDED.value

    logs = client.get("/api/admin/audit-logs")
    assert logs.status_code == 200
    actions = {item["action"] for item in logs.json()["items"]}
    assert "approve_listing" in actions
    assert "reject_listing" in actions

    filtered = client.get("/api/admin/audit-logs", params={"action": "approve_listing"})
    assert filtered.status_code == 200
    assert filtered.json()["total"] >= 1
    assert all(i["action"] == "approve_listing" for i in filtered.json()["items"])


def test_dispute_list_includes_72h_sla_and_three_resolve_paths(
    client: TestClient,
) -> None:
    booking = _insert_booking(status=BookingStatus.DISPUTED, total_pence=20_000)
    _auth(ADMIN)
    listed = client.get("/api/admin/disputes")
    assert listed.status_code == 200
    items = listed.json()["items"]
    match = next(i for i in items if i["booking_id"] == booking.id)
    due = datetime.fromisoformat(match["first_decision_due_at"].replace("Z", "+00:00"))
    delta = due - datetime.now(timezone.utc)
    assert timedelta(hours=71) < delta <= timedelta(hours=72, minutes=2)
    assert match["under_value_threshold"] is True

    resolved = client.post(
        f"/api/admin/bookings/{booking.id}/resolve-dispute",
        json={"resolution": "approve_seller", "reason": "Proof accepted"},
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == BookingStatus.COMPLETED.value

    invalid = client.post(
        f"/api/admin/bookings/{booking.id}/resolve-dispute",
        json={"resolution": "split_the_difference", "reason": "nope"},
    )
    assert invalid.status_code == 422


# --- B8 analytics own-data ---


def test_buyer_analytics_own_data_only(client: TestClient) -> None:
    _insert_booking(
        status=BookingStatus.LIVE,
        buyer_id="buyer-1",
        total_pence=8_000,
        booking_cis=90.0,
    )
    _insert_booking(
        status=BookingStatus.COMPLETED,
        buyer_id="buyer-2",
        total_pence=50_000,
        booking_cis=10.0,
    )
    _auth(BUYER)
    response = client.get("/api/analytics/buyer")
    assert response.status_code == 200
    body = response.json()
    assert body["spend_30d_pence"] == 8_000
    assert body["active_campaigns"] == 1
    assert body["avg_cis_received"] == 90.0
    assert all(c["total_pence"] != 50_000 for c in body["campaigns"])

    _auth(OTHER_BUYER)
    other = client.get("/api/analytics/buyer")
    assert other.status_code == 200
    assert other.json()["spend_30d_pence"] == 50_000


def test_seller_analytics_own_data_only(client: TestClient) -> None:
    other_listing = store.create_listing(
        ListingRecord(
            id=new_id(),
            seller_id="seller-other",
            title="Other gym",
            description="x",
            category=Category.GYM,
            status=ListingStatus.PUBLISHED,
            price_per_day_pence=1000,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/g.webp"],
            moderation_status="approved",
        )
    )
    store.upsert_seller(SellerProfile(user_id="seller-other"))
    _insert_booking(
        status=BookingStatus.COMPLETED,
        seller_id="seller-seed-1",
        total_pence=10_000,
        commission_pence=1_000,
        booking_cis=88.0,
    )
    _insert_booking(
        status=BookingStatus.LIVE,
        seller_id="seller-seed-1",
        total_pence=4_000,
        commission_pence=400,
        booking_cis=None,
    )
    _insert_booking(
        status=BookingStatus.COMPLETED,
        seller_id="seller-other",
        listing_id=other_listing.id,
        total_pence=99_000,
        commission_pence=9_900,
        booking_cis=20.0,
    )
    _auth(SELLER)
    response = client.get("/api/analytics/seller")
    assert response.status_code == 200
    body = response.json()
    assert body["revenue_30d_pence"] == 9_000
    assert body["pending_payouts_pence"] == 3_600
    assert 0 <= body["occupancy_rate"] <= 1
    assert len(body["revenue_12m_series"]) == 12
    assert len(body["cis_trend"]) == 12
    assert body["revenue_30d_pence"] != 89_100

    _auth(BUYER)
    forbidden = client.get("/api/analytics/seller")
    assert forbidden.status_code == 403


# --- B9 public stats ---


def test_public_stats_unauthenticated_and_cached(client: TestClient) -> None:
    first = client.get("/api/public/stats")
    assert first.status_code == 200
    body = first.json()
    assert body["listing_count"] >= 1
    assert any(c["category"] == Category.BILLBOARD.value for c in body["categories"])
    assert any(f["id"] == "listing-seed-1" for f in body["featured"])

    store.create_listing(
        ListingRecord(
            id=new_id(),
            seller_id="seller-seed-1",
            title="Cached out",
            description="should not appear until cache expires",
            category=Category.CAFE,
            status=ListingStatus.PUBLISHED,
            price_per_day_pence=1000,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/c.webp"],
            is_featured=True,
            moderation_status="approved",
        )
    )
    cached = client.get("/api/public/stats")
    assert cached.json()["listing_count"] == body["listing_count"]

    clear_cache()
    fresh = client.get("/api/public/stats")
    assert fresh.json()["listing_count"] == body["listing_count"] + 1


# --- B7 verification ---


def test_seller_verification_submit_and_admin_review(client: TestClient) -> None:
    _auth(SELLER)
    submitted = client.post(
        "/api/verification/seller",
        json={
            "business_name": "Shoreditch Screens Ltd",
            "company_number": "12345678",
            "notes": "VAT registered",
            "document_urls": ["https://example.com/cert.pdf"],
        },
    )
    assert submitted.status_code == 201
    assert submitted.json()["status"] == "pending"
    assert submitted.json()["is_verified"] is False

    mine = client.get("/api/verification/seller")
    assert mine.json()["status"] == "pending"

    _auth(ADMIN)
    pending = client.get("/api/verification/admin/pending")
    assert pending.status_code == 200
    assert any(i["seller_id"] == "seller-seed-1" for i in pending.json()["items"])

    reviewed = client.post(
        "/api/verification/admin/seller-seed-1/review",
        json={"status": "verified", "reason": "Companies House match"},
    )
    assert reviewed.status_code == 200
    assert reviewed.json()["status"] == "verified"
    assert reviewed.json()["is_verified"] is True

    logs = client.get("/api/admin/audit-logs", params={"action": "review_seller_verification"})
    assert logs.json()["total"] >= 1


def test_buyer_account_type_capture(client: TestClient) -> None:
    _auth(BUYER)
    empty = client.get("/api/verification/buyer/account-type")
    assert empty.status_code == 200
    assert empty.json()["account_type"] is None

    updated = client.put(
        "/api/verification/buyer/account-type",
        json={"account_type": "agency"},
    )
    assert updated.status_code == 200
    assert updated.json()["account_type"] == "agency"

    invalid = client.put(
        "/api/verification/buyer/account-type",
        json={"account_type": "hobbyist"},
    )
    assert invalid.status_code == 422


# --- B11 attribution ---


def test_attribution_code_scan_and_redirect(client: TestClient) -> None:
    booking = _insert_booking(status=BookingStatus.CONFIRMED)
    other = _insert_booking(status=BookingStatus.CONFIRMED, buyer_id="buyer-2")
    assert booking.id != other.id

    _auth(BUYER)
    attr = client.get(f"/api/bookings/{booking.id}/attribution")
    assert attr.status_code == 200
    code = attr.json()["code"]
    assert code.startswith("MP")
    assert attr.json()["scan_count"] == 0
    assert attr.json()["redemption_count"] == 0
    assert attr.json()["target_url"] == "https://marketplays.com"

    _auth(OTHER_BUYER)
    other_code = client.get(f"/api/bookings/{other.id}/attribution").json()["code"]
    assert other_code != code

    forbidden = client.get(f"/api/bookings/{booking.id}/attribution")
    assert forbidden.status_code == 403

    app.dependency_overrides.clear()
    redirect = client.get(f"/api/attribution/r/{code}", follow_redirects=False)
    assert redirect.status_code == 302
    assert redirect.headers["location"] == "https://marketplays.com"

    _auth(BUYER)
    after = client.get(f"/api/bookings/{booking.id}/attribution")
    assert after.json()["scan_count"] == 1

    missing = client.get("/api/attribution/r/NOTACODE", follow_redirects=False)
    assert missing.status_code == 404
