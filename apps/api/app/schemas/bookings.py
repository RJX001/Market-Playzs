"""Booking and review schemas. Clients never send status patches."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain_enums import BookingStatus


class BookingCreate(BaseModel):
    listing_id: str
    start_date: date
    end_date: date


class BookingCreateResponse(BaseModel):
    booking_id: str
    client_secret: str
    status: BookingStatus
    total_pence: int


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    status: BookingStatus
    start_date: date
    end_date: date
    total_pence: int
    commission_pence: int
    stripe_payment_intent_id: str | None
    stripe_transfer_id: str | None
    delivery_score: float | None
    rating: int | None
    booking_cis: float | None
    created_at: datetime
    updated_at: datetime


class BookingListResponse(BaseModel):
    items: list[BookingResponse]
    total: int


class ReviewCreate(BaseModel):
    rating: int = Field(ge=1, le=5)
    delivery_score: float = Field(description="Exactly 0, 0.5, or 1")
    comment: str | None = Field(default=None, max_length=2000)


class ReviewResponse(BaseModel):
    booking_id: str
    listing_id: str
    rating: int
    delivery_score: float
    listing_cis: int | None
    status: BookingStatus
