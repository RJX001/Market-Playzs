"""B3 notifications + B4 favourites + B5 saved-search API tests."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.deps import CurrentUser, get_current_user
from app.api.notifications import register_engagement_routers
from app.domain_enums import BookingStatus, UserRole
from app.repositories.memory_store import BookingRecord, new_id, store
from app.services import (
    booking_service,
    favourite_service,
    notification_service,
    saved_search_service,
)


def _user(
    user_id: str = "buyer-1",
    role: UserRole = UserRole.BUYER,
    email: str = "buyer@example.com",
) -> CurrentUser:
    return CurrentUser(id=user_id, role=role, email=email)


def _client_for(user: CurrentUser) -> TestClient:
    app = FastAPI()
    register_engagement_routers(app)

    async def _override() -> CurrentUser:
        return user

    app.dependency_overrides[get_current_user] = _override
    return TestClient(app)


@pytest.fixture(autouse=True)
def _reset_engagement() -> None:
    notification_service.reset_store()
    favourite_service.reset_store()
    saved_search_service.reset_store()
    yield
    notification_service.reset_store()
    favourite_service.reset_store()
    saved_search_service.reset_store()


@pytest.fixture
def buyer_client() -> TestClient:
    return _client_for(_user("buyer-1", UserRole.BUYER, "buyer@example.com"))


@pytest.fixture
def seller_client() -> TestClient:
    return _client_for(
        _user("seller-seed-1", UserRole.SELLER, "seller@example.com")
    )


def _booking(
    *,
    buyer_id: str = "buyer-1",
    seller_id: str = "seller-seed-1",
    status: BookingStatus = BookingStatus.CONFIRMED,
    rating: int | None = None,
) -> BookingRecord:
    rec = BookingRecord(
        id=new_id(),
        listing_id="listing-seed-1",
        buyer_id=buyer_id,
        seller_id=seller_id,
        status=status,
        start_date=date.today(),
        end_date=date.today() + timedelta(days=1),
        total_pence=5000,
        commission_pence=500,
        rating=rating,
    )
    return store.create_booking(rec)


def test_notifications_require_auth() -> None:
    app = FastAPI()
    register_engagement_routers(app)
    client = TestClient(app)
    assert client.get("/api/notifications").status_code == 401
    assert client.post("/api/notifications/mark-read", json={"mark_all": True}).status_code == 401


def test_list_notifications_empty(buyer_client: TestClient) -> None:
    response = buyer_client.get("/api/notifications")
    assert response.status_code == 200
    body = response.json()
    assert body["items"] == []
    assert body["total"] == 0
    assert body["unread_count"] == 0
    assert body["page"] == 1


def test_ownership_hides_other_users_notifications(
    buyer_client: TestClient, seller_client: TestClient
) -> None:
    booking = _booking()
    notification_service.notify_new_booking(
        booking, seller_email="seller@example.com"
    )
    seller_list = seller_client.get("/api/notifications").json()
    buyer_list = buyer_client.get("/api/notifications").json()
    assert seller_list["total"] == 1
    assert seller_list["unread_count"] == 1
    assert buyer_list["total"] == 0


def test_mark_read_bulk_and_mark_all(seller_client: TestClient) -> None:
    booking = _booking()
    notification_service.notify_new_booking(booking)
    notification_service.notify_booking_cancelled(booking)
    listed = seller_client.get("/api/notifications").json()
    assert listed["unread_count"] == 2
    first_id = listed["items"][0]["id"]
    marked = seller_client.post(
        "/api/notifications/mark-read", json={"ids": [first_id]}
    )
    assert marked.status_code == 200
    assert marked.json()["marked_count"] == 1
    assert marked.json()["unread_count"] == 1
    all_read = seller_client.post(
        "/api/notifications/mark-read", json={"mark_all": True}
    )
    assert all_read.json()["unread_count"] == 0
    assert seller_client.get("/api/notifications").json()["unread_count"] == 0


def test_mark_read_requires_ids_or_flag(buyer_client: TestClient) -> None:
    response = buyer_client.post("/api/notifications/mark-read", json={})
    assert response.status_code == 400


def test_pagination_and_unread_count(seller_client: TestClient) -> None:
    booking = _booking()
    for _ in range(3):
        notification_service.notify_new_booking(booking)
    page1 = seller_client.get("/api/notifications", params={"page": 1, "page_size": 2})
    body = page1.json()
    assert body["total"] == 3
    assert len(body["items"]) == 2
    assert body["unread_count"] == 3
    page2 = seller_client.get("/api/notifications", params={"page": 2, "page_size": 2})
    assert len(page2.json()["items"]) == 1


def test_seller_and_buyer_emitters() -> None:
    booking = _booking(rating=5)
    notification_service.notify_new_booking(booking)
    notification_service.notify_booking_cancelled(booking)
    notification_service.notify_payment_released(booking)
    notification_service.notify_review_received(booking)
    notification_service.notify_booking_confirmed(booking)
    notification_service.notify_campaign_live(booking)
    notification_service.notify_campaign_complete(booking)
    notification_service.notify_review_reminder(booking)

    seller_rows, seller_total, _ = notification_service.list_notifications(
        "seller-seed-1"
    )
    buyer_rows, buyer_total, _ = notification_service.list_notifications("buyer-1")
    seller_types = {row.event_type.value for row in seller_rows}
    buyer_types = {row.event_type.value for row in buyer_rows}
    assert seller_total == 4
    assert buyer_total == 4
    assert seller_types == {
        "new_booking",
        "booking_cancelled",
        "payment_released",
        "review_received",
    }
    assert buyer_types == {
        "booking_confirmed",
        "campaign_live",
        "campaign_complete",
        "review_reminder",
    }


def test_status_change_and_completed_hooks() -> None:
    confirmed = _booking(status=BookingStatus.PENDING_PAYMENT)
    notification_service.notify_status_change(
        confirmed.id, BookingStatus.CONFIRMED, actor="test"
    )
    live = _booking(status=BookingStatus.CONFIRMED)
    notification_service.notify_status_change(
        live.id, BookingStatus.LIVE, actor="test"
    )
    cancelled = _booking(status=BookingStatus.CONFIRMED)
    notification_service.notify_status_change(
        cancelled.id, BookingStatus.CANCELLED, actor="test"
    )
    awaiting = _booking(status=BookingStatus.AWAITING_BUYER_REVIEW)
    notification_service.notify_status_change(
        awaiting.id, BookingStatus.AWAITING_BUYER_REVIEW, actor="test"
    )
    completed = _booking(status=BookingStatus.COMPLETED, rating=4)
    notification_service.notify_booking_completed(completed)

    _, seller_total, _ = notification_service.list_notifications("seller-seed-1")
    _, buyer_total, _ = notification_service.list_notifications("buyer-1")
    assert seller_total == 3  # cancelled + payment_released + review_received
    assert buyer_total == 4  # confirmed, live, reminder, complete


def test_create_booking_emits_seller_new_booking() -> None:
    start = date.today()
    end = start + timedelta(days=1)
    booking, _secret = booking_service.create_booking(
        listing_id="listing-seed-1",
        buyer_id="buyer-1",
        start_date=start,
        end_date=end,
    )
    rows, total, unread = notification_service.list_notifications("seller-seed-1")
    assert total == 1
    assert unread == 1
    assert rows[0].event_type.value == "new_booking"
    assert rows[0].booking_id == booking.id


def test_email_logged_and_sendgrid_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    booking = _booking()
    notification_service.notify_booking_confirmed(
        booking, buyer_email="buyer@example.com"
    )
    log = notification_service.get_email_log()
    assert len(log) == 1
    assert log[0]["to_email"] == "buyer@example.com"
    assert "confirmed" in log[0]["subject"].lower()

    monkeypatch.setenv("SENDGRID_API_KEY", "sg-test-key")
    with patch("app.services.notification_service.httpx.post") as mocked:
        mocked.return_value.status_code = 202
        mocked.return_value.text = ""
        notification_service.notify_campaign_live(
            booking, buyer_email="buyer@example.com"
        )
        mocked.assert_called_once()
        args, kwargs = mocked.call_args
        assert args[0] == notification_service.SENDGRID_MAIL_URL
        assert "Bearer sg-test-key" in kwargs["headers"]["Authorization"]


def test_background_tasks_do_not_block() -> None:
    import asyncio

    from fastapi import BackgroundTasks

    booking = _booking()
    tasks = BackgroundTasks()
    notification_service.notify_new_booking(
        booking, background_tasks=tasks, seller_email="seller@example.com"
    )
    assert notification_service.get_email_log() == []
    asyncio.run(tasks())
    assert len(notification_service.get_email_log()) == 1


def test_favourites_crud_and_ownership(buyer_client: TestClient) -> None:
    created = buyer_client.post("/api/favourites/listing-seed-1")
    assert created.status_code == 201
    body = created.json()
    assert body["listing_id"] == "listing-seed-1"
    assert body["title"] == "Seed Billboard — Shoreditch"

    again = buyer_client.post("/api/favourites/listing-seed-1")
    assert again.status_code == 200
    assert again.json()["id"] == body["id"]

    listed = buyer_client.get("/api/favourites")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1

    other = _client_for(_user("buyer-2"))
    assert other.get("/api/favourites").json()["total"] == 0
    assert other.delete("/api/favourites/listing-seed-1").status_code == 404

    deleted = buyer_client.delete("/api/favourites/listing-seed-1")
    assert deleted.status_code == 204
    assert buyer_client.get("/api/favourites").json()["total"] == 0


def test_favourite_unknown_listing(buyer_client: TestClient) -> None:
    response = buyer_client.post("/api/favourites/does-not-exist")
    assert response.status_code == 404


def test_saved_searches_crud_and_ownership(buyer_client: TestClient) -> None:
    filters: dict[str, Any] = {
        "categories": ["billboard"],
        "radius_km": 5,
        "cis_min": 70,
        "price_max_pence": 10000,
    }
    created = buyer_client.post(
        "/api/saved-searches",
        json={"name": "Shoreditch boards", "filters": filters},
    )
    assert created.status_code == 201
    body = created.json()
    assert body["name"] == "Shoreditch boards"
    assert body["filters"] == filters
    search_id = body["id"]

    listed = buyer_client.get("/api/saved-searches")
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == search_id

    other = _client_for(_user("buyer-2"))
    assert other.get("/api/saved-searches").json()["total"] == 0
    assert other.delete(f"/api/saved-searches/{search_id}").status_code == 404

    deleted = buyer_client.delete(f"/api/saved-searches/{search_id}")
    assert deleted.status_code == 204
    assert buyer_client.get("/api/saved-searches").json()["total"] == 0
    assert buyer_client.delete(f"/api/saved-searches/{search_id}").status_code == 404


def test_openapi_summaries(buyer_client: TestClient) -> None:
    spec = buyer_client.app.openapi()  # type: ignore[attr-defined]
    paths = spec["paths"]
    assert paths["/api/notifications"]["get"]["summary"]
    assert paths["/api/notifications/mark-read"]["post"]["summary"]
    assert paths["/api/favourites"]["get"]["summary"]
    assert paths["/api/favourites/{listing_id}"]["post"]["summary"]
    assert paths["/api/favourites/{listing_id}"]["delete"]["summary"]
    assert paths["/api/saved-searches"]["get"]["summary"]
    assert paths["/api/saved-searches"]["post"]["summary"]
    assert paths["/api/saved-searches/{search_id}"]["delete"]["summary"]
