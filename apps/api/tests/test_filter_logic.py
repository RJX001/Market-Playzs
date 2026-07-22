"""Filter logic tests — Section 5.4."""

from __future__ import annotations

from app.domain_enums import Category, ListingStatus
from app.repositories.memory_store import ListingRecord, new_id, store
from app.services import listing_service


def test_empty_filter_returns_published_in_default_bbox() -> None:
    items, total = listing_service.search_listings()
    assert total >= 1
    assert all(i.status == ListingStatus.PUBLISHED for i in items)


def test_draft_and_suspended_excluded() -> None:
    store.create_listing(
        ListingRecord(
            id=new_id(),
            seller_id="seller-seed-1",
            title="Draft",
            description="x",
            category=Category.CAFE,
            status=ListingStatus.DRAFT,
            price_per_day_pence=1000,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/a.webp"],
        )
    )
    store.create_listing(
        ListingRecord(
            id=new_id(),
            seller_id="seller-seed-1",
            title="Suspended",
            description="x",
            category=Category.CAFE,
            status=ListingStatus.SUSPENDED,
            price_per_day_pence=1000,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/a.webp"],
        )
    )
    items, _ = listing_service.search_listings()
    assert all(i.status == ListingStatus.PUBLISHED for i in items)
    assert all(i.title not in {"Draft", "Suspended"} for i in items)


def test_null_cis_included_in_cis_tier() -> None:
    store.update_listing("listing-seed-1", cis_score=None)
    items, total = listing_service.search_listings(cis_min=70, cis_max=100)
    assert total >= 1
    assert any(i.id == "listing-seed-1" for i in items)


def test_category_or_within_multiselect() -> None:
    store.create_listing(
        ListingRecord(
            id=new_id(),
            seller_id="seller-seed-1",
            title="Gym Spot",
            description="x",
            category=Category.GYM,
            status=ListingStatus.PUBLISHED,
            price_per_day_pence=1200,
            lat=51.51,
            lng=-0.12,
            images=["https://example.com/g.webp"],
        )
    )
    items, _ = listing_service.search_listings(
        categories=[Category.GYM, Category.CAFE]
    )
    assert any(i.category == Category.GYM for i in items)
    assert all(
        i.category in {Category.GYM, Category.CAFE} for i in items
    )
