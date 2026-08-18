"""Filter logic tests — Section 5.4. Also A4 publish guard + B6 media."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.domain_enums import Category, ListingStatus
from app.repositories.memory_store import (
    ListingRecord,
    SellerProfile,
    new_id,
    store,
)
from app.services import listing_service, media_service
from app.services.listing_service import (
    ListingForbiddenError,
    ListingNotFoundError,
    ListingServiceError,
)
from app.services.media_service import MediaServiceError

# 1×1 PNG (magic bytes sufficient for sniff_mime)
_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00"
    b"\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


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


def test_audience_and_booking_type_filters() -> None:
    items, total = listing_service.search_listings(audience_tags=["local"])
    assert total >= 1
    assert all("local" in i.audience_tags for i in items)

    items, total = listing_service.search_listings(booking_types=["instant"])
    assert total >= 1
    assert all("instant" in i.booking_types for i in items)

    items, total = listing_service.search_listings(audience_tags=["no-such-tag"])
    assert total == 0


def test_price_and_radius_and_dates() -> None:
    items, total = listing_service.search_listings(
        price_min_pence=2000, price_max_pence=3000
    )
    assert total >= 1
    assert all(2000 <= i.price_per_day_pence <= 3000 for i in items)

    items, total = listing_service.search_listings(
        price_min_pence=9000, price_max_pence=10000
    )
    assert total == 0

    # Seed listing is in Shoreditch — tight radius around it matches
    items, total = listing_service.search_listings(
        center_lat=51.5255, center_lng=-0.0815, radius_km=1
    )
    assert total >= 1
    assert any(i.id == "listing-seed-1" for i in items)

    items, total = listing_service.search_listings(
        center_lat=0.0, center_lng=0.0, radius_km=1
    )
    assert all(i.id != "listing-seed-1" for i in items)

    start = date.today()
    end = start + timedelta(days=2)
    items, total = listing_service.search_listings(
        available_from=start, available_to=end
    )
    assert total >= 1
    assert any(i.id == "listing-seed-1" for i in items)

    far = start + timedelta(days=400)
    items, total = listing_service.search_listings(
        available_from=far, available_to=far + timedelta(days=2)
    )
    assert all(i.id != "listing-seed-1" for i in items)


def test_sort_price_and_invalid() -> None:
    store.create_listing(
        ListingRecord(
            id=new_id(),
            seller_id="seller-seed-1",
            title="Cheap Cafe",
            description="x",
            category=Category.CAFE,
            status=ListingStatus.PUBLISHED,
            price_per_day_pence=100,
            lat=51.52,
            lng=-0.10,
            images=["https://example.com/c.webp"],
        )
    )
    items, _ = listing_service.search_listings(sort="price_asc")
    prices = [i.price_per_day_pence for i in items]
    assert prices == sorted(prices)

    items, _ = listing_service.search_listings(sort="price_desc")
    prices = [i.price_per_day_pence for i in items]
    assert prices == sorted(prices, reverse=True)

    with pytest.raises(ListingServiceError, match="Invalid sort"):
        listing_service.search_listings(sort="not_a_sort")


def test_buyer_get_hides_draft_owner_can_read() -> None:
    draft = store.create_listing(
        ListingRecord(
            id=new_id(),
            seller_id="seller-seed-1",
            title="Owner Draft",
            description="x",
            category=Category.CAFE,
            status=ListingStatus.DRAFT,
            price_per_day_pence=1000,
            lat=51.5,
            lng=-0.1,
            images=["https://example.com/a.webp"],
        )
    )
    with pytest.raises(ListingNotFoundError):
        listing_service.get_listing_for_viewer(draft.id, requester_id=None)
    with pytest.raises(ListingNotFoundError):
        listing_service.get_listing_for_viewer(draft.id, requester_id="buyer-1")
    owned = listing_service.get_listing_for_viewer(
        draft.id, requester_id="seller-seed-1"
    )
    assert owned.status == ListingStatus.DRAFT


def test_publish_guard_stripe_image_and_ownership() -> None:
    draft = listing_service.create_listing_draft(
        "seller-seed-1",
        {
            "title": "New Space",
            "description": "A complete draft",
            "category": Category.SHOP,
            "price_per_day_pence": 1500,
            "lat": 51.5,
            "lng": -0.1,
            "images": [],
        },
    )
    with pytest.raises(ListingServiceError, match="image"):
        listing_service.publish_listing(draft.id, "seller-seed-1")

    store.update_listing(draft.id, images=["https://example.com/p.webp"])
    with pytest.raises(ListingForbiddenError):
        listing_service.publish_listing(draft.id, "not-the-owner")

    store.upsert_seller(
        SellerProfile(
            user_id="seller-no-stripe",
            stripe_account_id=None,
            stripe_charges_enabled=False,
        )
    )
    orphan = listing_service.create_listing_draft(
        "seller-no-stripe",
        {
            "title": "Unconnected",
            "description": "no stripe",
            "category": Category.SHOP,
            "price_per_day_pence": 1500,
            "lat": 51.5,
            "lng": -0.1,
            "images": ["https://example.com/p.webp"],
        },
    )
    with pytest.raises(ListingServiceError, match="Stripe"):
        listing_service.publish_listing(orphan.id, "seller-no-stripe")

    published = listing_service.publish_listing(draft.id, "seller-seed-1")
    assert published.status == ListingStatus.PUBLISHED


def test_publish_rejects_suspended() -> None:
    rec = listing_service.create_listing_draft(
        "seller-seed-1",
        {
            "title": "Will Suspend",
            "description": "x",
            "category": Category.SHOP,
            "price_per_day_pence": 1500,
            "lat": 51.5,
            "lng": -0.1,
            "images": ["https://example.com/p.webp"],
        },
    )
    store.update_listing(rec.id, status=ListingStatus.SUSPENDED)
    with pytest.raises(ListingServiceError, match="Suspended"):
        listing_service.publish_listing(rec.id, "seller-seed-1")


def test_media_upload_sniffs_mime_and_rejects_bad_type(
    tmp_path, monkeypatch
) -> None:
    monkeypatch.setattr(media_service, "UPLOAD_DIR", tmp_path)
    record = media_service.save_upload(
        _PNG, original_filename="slot.png", purpose="listing_image"
    )
    assert record.mime_type == "image/png"
    assert record.url == f"/api/media/{record.id}"
    assert (tmp_path / f"{record.id}.png").is_file()

    loaded, path = media_service.get_media(record.id)
    assert loaded.id == record.id
    assert path.is_file()

    with pytest.raises(MediaServiceError, match="Unsupported"):
        media_service.save_upload(
            b"not-an-image-at-all!!",
            original_filename="x.jpg",
            purpose="listing_image",
        )

    # Video magic is allowed for proof, not listing images
    mp4 = b"\x00\x00\x00\x18ftypisom" + b"\x00" * 8
    with pytest.raises(MediaServiceError, match="Unsupported"):
        media_service.save_upload(
            mp4, original_filename="clip.mp4", purpose="listing_image"
        )
    proof = media_service.save_upload(
        mp4, original_filename="clip.mp4", purpose="proof"
    )
    assert proof.mime_type == "video/mp4"
    assert proof.purpose == "proof"

    media_service.generate_thumbnail_stub(record.id)


def test_media_size_cap(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(media_service, "UPLOAD_DIR", tmp_path)
    too_big = b"\xff\xd8\xff" + b"\x00" * media_service.IMAGE_MAX_BYTES
    with pytest.raises(MediaServiceError, match="size cap"):
        media_service.save_upload(
            too_big, original_filename="huge.jpg", purpose="listing_image"
        )
