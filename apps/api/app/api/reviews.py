"""Public listing reviews. Booking review POST stays on bookings.py."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.schemas.reviews import ListingReviewItem, ListingReviewsResponse
from app.services import review_service
from app.services.review_service import ReviewServiceError

router = APIRouter(prefix="/api/listings", tags=["reviews"])


@router.get(
    "/{listing_id}/reviews",
    response_model=ListingReviewsResponse,
    summary="List reviews for a listing",
    description=(
        "Paginated public reviews for a published listing page. "
        "Includes the listing's current CIS score (null means New). "
        "Draft and suspended listings are treated as not found. "
        "Buyer review submission remains POST /api/bookings/{id}/review."
    ),
)
async def list_listing_reviews(
    listing_id: str,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
) -> ListingReviewsResponse:
    try:
        items, total, listing_cis = review_service.list_listing_reviews(
            listing_id, page=page, page_size=page_size
        )
    except ReviewServiceError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    return ListingReviewsResponse(
        listing_id=listing_id,
        listing_cis=listing_cis,
        items=[
            ListingReviewItem(
                id=r.id,
                booking_id=r.booking_id,
                listing_id=r.listing_id,
                rating=r.rating,
                comment=r.comment,
                created_at=r.created_at,
            )
            for r in items
        ],
        total=total,
        page=page,
        page_size=page_size,
    )
