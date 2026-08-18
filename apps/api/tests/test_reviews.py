"""Listing reviews API — public GET. POST review stays on bookings."""

from __future__ import annotations

from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.reviews import router as reviews_router
from app.domain_enums import BookingStatus, Category, ListingStatus
from app.repositories.memory_store import (
    BookingRecord,
    ListingRecord,
    ReviewRecord,
    new_id,
    store,
)
from app.services import cis_service, review_service
from app.services.review_service import ReviewServiceError


def _app_client() -> TestClient:
    app = FastAPI()
    app.include_router(reviews_router)
    return TestClient(app)


def _add_review(
    *,
    listing_id: str = "listing-seed-1",
    rating: int = 5,
    comment: str | None = "Great placement",
) -> ReviewRecord:
    return store.create_review(
        ReviewRecord(
            id=new_id(),
            booking_id=new_id(),
            listing_id=listing_id,
            buyer_id="buyer-1",
            rating=rating,
            delivery_score=1.0,
            comment=comment,
        )
    )


def test_list_listing_reviews_empty() -> None:
    items, total, listing_cis = review_service.list_listing_reviews("listing-seed-1")
    assert items == []
    assert total == 0
    assert listing_cis is None


def test_list_listing_reviews_paginated_newest_first() -> None:
    first = _add_review(comment="older")
    second = _add_review(comment="newer")
    items, total, _ = review_service.list_listing_reviews(
        "listing-seed-1", page=1, page_size=1
    )
    assert total == 2
    assert len(items) == 1
    assert items[0].id == second.id
    page2, _, _ = review_service.list_listing_reviews(
        "listing-seed-1", page=2, page_size=1
    )
    assert page2[0].id == first.id


def test_list_listing_reviews_includes_listing_cis() -> None:
    start = date.today()
    store.create_booking(
        BookingRecord(
            id=new_id(),
            listing_id="listing-seed-1",
            buyer_id="buyer-1",
            seller_id="seller-seed-1",
            status=BookingStatus.COMPLETED,
            start_date=start,
            end_date=start + timedelta(days=1),
            total_pence=5000,
            booking_cis=80.0,
        )
    )
    cis_service.recalculate_listing_cis("listing-seed-1")
    _add_review(rating=4, comment="solid")
    items, total, listing_cis = review_service.list_listing_reviews("listing-seed-1")
    assert total == 1
    assert items[0].rating == 4
    assert listing_cis == 80


def test_list_listing_reviews_unknown_listing() -> None:
    try:
        review_service.list_listing_reviews("missing")
        raise AssertionError("expected ReviewServiceError")
    except ReviewServiceError as exc:
        assert "not found" in str(exc).lower()


def test_list_listing_reviews_unpublished_hidden() -> None:
    draft_id = new_id()
    store.create_listing(
        ListingRecord(
            id=draft_id,
            seller_id="seller-seed-1",
            title="Draft",
            description="hidden",
            category=Category.CAFE,
            status=ListingStatus.DRAFT,
            price_per_day_pence=1000,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/a.webp"],
        )
    )
    _add_review(listing_id=draft_id, comment="should not leak")
    try:
        review_service.list_listing_reviews(draft_id)
        raise AssertionError("expected ReviewServiceError")
    except ReviewServiceError:
        pass


def test_get_listing_reviews_http_public() -> None:
    _add_review(comment="on the listing page")
    client = _app_client()
    res = client.get("/api/listings/listing-seed-1/reviews")
    assert res.status_code == 200
    body = res.json()
    assert body["listing_id"] == "listing-seed-1"
    assert body["total"] == 1
    assert body["items"][0]["comment"] == "on the listing page"
    assert body["items"][0]["rating"] == 5
    assert "listing_cis" in body


def test_get_listing_reviews_http_404() -> None:
    client = _app_client()
    res = client.get("/api/listings/does-not-exist/reviews")
    assert res.status_code == 404
