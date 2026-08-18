"""Public listing review schemas. Booking review create lives on bookings."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ListingReviewItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    booking_id: str
    listing_id: str
    rating: int
    comment: str | None
    created_at: datetime


class ListingReviewsResponse(BaseModel):
    listing_id: str
    listing_cis: int | None
    items: list[ListingReviewItem]
    total: int
    page: int
    page_size: int
