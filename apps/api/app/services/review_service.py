"""Public listing reviews — read path only.

POST /api/bookings/{id}/review lives on booking_service.submit_review.
This module lists stored reviews + listing CIS for the listing page.
"""

from __future__ import annotations

from app.domain_enums import ListingStatus
from app.repositories.memory_store import ReviewRecord, store


class ReviewServiceError(ValueError):
    """Domain validation error for review listing operations."""


def list_listing_reviews(
    listing_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ReviewRecord], int, int | None]:
    """
    Paginated public reviews for a published listing.

    Returns (items, total, listing_cis). listing_cis is the stored CIS score
    (nullable = "New"); it is not recomputed here.
    """
    listing = store.get_listing(listing_id)
    if not listing or listing.status != ListingStatus.PUBLISHED:
        raise ReviewServiceError("Listing not found")

    all_reviews = store.list_reviews_for_listing(listing_id)
    total = len(all_reviews)
    start = (page - 1) * page_size
    items = all_reviews[start : start + page_size]
    return items, total, listing.cis_score
