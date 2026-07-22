"""Listing search (Section 5.4) and publish guard (Section 5.5 / 7)."""

from __future__ import annotations

import math
from datetime import date

from app.domain_enums import Category, ListingStatus
from app.repositories.memory_store import ListingRecord, new_id, store
from app.services import notification_service

# Default viewport when empty filter request (Greater London-ish)
DEFAULT_BBOX = {
    "min_lng": -0.5,
    "min_lat": 51.3,
    "max_lng": 0.3,
    "max_lat": 51.7,
}

PAGE_SIZE_MAX = 20


class ListingServiceError(ValueError):
    pass


def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    )
    return 2 * r * math.asin(math.sqrt(a))


def _in_bbox(
    listing: ListingRecord,
    min_lng: float,
    min_lat: float,
    max_lng: float,
    max_lat: float,
) -> bool:
    return (
        min_lng <= listing.lng <= max_lng
        and min_lat <= listing.lat <= max_lat
    )


def search_listings(
    *,
    min_lng: float | None = None,
    min_lat: float | None = None,
    max_lng: float | None = None,
    max_lat: float | None = None,
    center_lng: float | None = None,
    center_lat: float | None = None,
    radius_km: float | None = None,
    categories: list[Category] | None = None,
    audience_tags: list[str] | None = None,
    booking_types: list[str] | None = None,
    price_min_pence: int | None = None,
    price_max_pence: int | None = None,
    cis_min: int | None = None,
    cis_max: int | None = None,
    include_new_cis: bool = True,
    available_from: date | None = None,
    available_to: date | None = None,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ListingRecord], int]:
    """
    Buyer map search: AND across filter types, OR within multi-selects.
    Always excludes draft/suspended. Null CIS included in CIS tiers by default.
    """
    page_size = min(max(page_size, 1), PAGE_SIZE_MAX)
    page = max(page, 1)

    has_bbox = all(v is not None for v in (min_lng, min_lat, max_lng, max_lat))
    has_radius = all(
        v is not None for v in (center_lng, center_lat, radius_km)
    )
    empty_filters = (
        not has_bbox
        and not has_radius
        and not categories
        and not audience_tags
        and not booking_types
        and price_min_pence is None
        and price_max_pence is None
        and cis_min is None
        and cis_max is None
        and available_from is None
        and available_to is None
    )

    # Empty / no spatial filter → default viewport bbox (Section 5.4)
    if empty_filters or (not has_bbox and not has_radius):
        min_lng = DEFAULT_BBOX["min_lng"]
        min_lat = DEFAULT_BBOX["min_lat"]
        max_lng = DEFAULT_BBOX["max_lng"]
        max_lat = DEFAULT_BBOX["max_lat"]
        has_bbox = True

    results: list[ListingRecord] = []
    for listing in store.list_listings():
        # Status gate — always
        if listing.status != ListingStatus.PUBLISHED:
            continue

        # Location: bbox AND (optional) radius
        if has_bbox:
            assert min_lng is not None and min_lat is not None
            assert max_lng is not None and max_lat is not None
            if not _in_bbox(listing, min_lng, min_lat, max_lng, max_lat):
                continue

        if has_radius:
            assert center_lat is not None and center_lng is not None
            assert radius_km is not None
            dist = _haversine_km(
                center_lat, center_lng, listing.lat, listing.lng
            )
            if dist > radius_km:
                continue

        # Multi-select OR within type
        if categories and listing.category not in categories:
            continue
        if audience_tags and not any(
            t in listing.audience_tags for t in audience_tags
        ):
            continue
        if booking_types and not any(
            t in listing.booking_types for t in booking_types
        ):
            continue

        # Price range
        if (
            price_min_pence is not None
            and listing.price_per_day_pence < price_min_pence
        ):
            continue
        if (
            price_max_pence is not None
            and listing.price_per_day_pence > price_max_pence
        ):
            continue

        # CIS tiers — null CIS included by default
        if cis_min is not None or cis_max is not None:
            if listing.cis_score is None:
                if not include_new_cis:
                    continue
            else:
                if cis_min is not None and listing.cis_score < cis_min:
                    continue
                if cis_max is not None and listing.cis_score > cis_max:
                    continue

        # Availability date range
        if available_from is not None and available_to is not None:
            rows = store.get_availability_for_range(
                listing.id, available_from, available_to
            )
            expected = (available_to - available_from).days + 1
            unlocked = [r for r in rows if not r.is_locked]
            if len(unlocked) < expected:
                continue

        results.append(listing)

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    return results[start:end], total


def publish_listing(listing_id: str, seller_id: str) -> ListingRecord:
    """
    Publish guard: Stripe connected, required fields complete, ≥1 image.
    """
    listing = store.get_listing(listing_id)
    if not listing:
        raise ListingServiceError("Listing not found")
    if listing.seller_id != seller_id:
        raise ListingServiceError("Only the listing owner may publish")

    errors: list[str] = []

    seller = store.get_seller(seller_id)
    if (
        not seller
        or not seller.stripe_account_id
        or not seller.stripe_charges_enabled
    ):
        errors.append("Stripe Connect account required")

    if not str(listing.title).strip():
        errors.append("Missing required field: title")
    if not str(listing.description).strip():
        errors.append("Missing required field: description")
    if listing.category is None:
        errors.append("Missing required field: category")
    if listing.price_per_day_pence is None or listing.price_per_day_pence < 0:
        errors.append("Missing required field: price_per_day_pence")
    if listing.lat is None or listing.lng is None:
        errors.append("Missing required field: lat/lng")

    if not listing.images:
        errors.append("At least one image required")

    if errors:
        raise ListingServiceError("; ".join(errors))

    updated = store.update_listing(
        listing_id, status=ListingStatus.PUBLISHED
    )
    assert updated is not None
    notification_service.notify_listing_published(listing_id, seller_id)
    return updated


def create_listing_draft(seller_id: str, data: dict) -> ListingRecord:
    record = ListingRecord(
        id=new_id(),
        seller_id=seller_id,
        title=data["title"],
        description=data["description"],
        category=data["category"],
        status=ListingStatus.DRAFT,
        price_per_day_pence=data["price_per_day_pence"],
        lat=data["lat"],
        lng=data["lng"],
        images=list(data.get("images") or []),
        cis_score=None,
        audience_tags=list(data.get("audience_tags") or []),
        booking_types=list(data.get("booking_types") or []),
    )
    return store.create_listing(record)


def update_listing_draft(
    listing_id: str, seller_id: str, data: dict
) -> ListingRecord:
    listing = store.get_listing(listing_id)
    if not listing:
        raise ListingServiceError("Listing not found")
    if listing.seller_id != seller_id:
        raise ListingServiceError("Only the listing owner may update")
    if listing.status == ListingStatus.SUSPENDED:
        raise ListingServiceError("Suspended listings cannot be edited by seller")

    payload = {k: v for k, v in data.items() if v is not None}
    updated = store.update_listing(listing_id, **payload)
    if not updated:
        raise ListingServiceError("Listing not found")
    return updated
