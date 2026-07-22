"""Listing request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.domain_enums import Category, ListingStatus


class ListingCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(min_length=1, max_length=5000)
    category: Category
    price_per_day_pence: int = Field(ge=0)
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    images: list[str] = Field(default_factory=list)
    audience_tags: list[str] = Field(default_factory=list)
    booking_types: list[str] = Field(default_factory=list)


class ListingUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, min_length=1, max_length=5000)
    category: Category | None = None
    price_per_day_pence: int | None = Field(default=None, ge=0)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    images: list[str] | None = None
    audience_tags: list[str] | None = None
    booking_types: list[str] | None = None


class ListingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    seller_id: str
    title: str
    description: str
    category: Category
    status: ListingStatus
    price_per_day_pence: int
    lat: float
    lng: float
    images: list[str]
    cis_score: int | None
    is_cis_overridden: bool
    audience_tags: list[str]
    booking_types: list[str]
    created_at: datetime
    updated_at: datetime


class ListingSearchResponse(BaseModel):
    items: list[ListingResponse]
    total: int
    page: int
    page_size: int


class PublishListingResponse(BaseModel):
    id: str
    status: ListingStatus
    message: str
