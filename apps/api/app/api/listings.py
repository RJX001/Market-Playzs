"""Listings API — search, CRUD stubs, publish guard."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import CurrentUser, require_role
from app.domain_enums import Category, ListingStatus, UserRole
from app.repositories.memory_store import store
from app.schemas.listings import (
    ListingCreate,
    ListingResponse,
    ListingSearchResponse,
    ListingUpdate,
    PublishListingResponse,
)
from app.services import listing_service
from app.services.listing_service import ListingServiceError

router = APIRouter(prefix="/api/listings", tags=["listings"])


def _to_response(listing) -> ListingResponse:
    return ListingResponse(
        id=listing.id,
        seller_id=listing.seller_id,
        title=listing.title,
        description=listing.description,
        category=listing.category,
        status=listing.status,
        price_per_day_pence=listing.price_per_day_pence,
        lat=listing.lat,
        lng=listing.lng,
        images=listing.images,
        cis_score=listing.cis_score,
        is_cis_overridden=listing.is_cis_overridden,
        audience_tags=listing.audience_tags,
        booking_types=listing.booking_types,
        created_at=listing.created_at,
        updated_at=listing.updated_at,
    )


@router.get("", response_model=ListingSearchResponse)
async def search_listings(
    min_lng: float | None = Query(default=None),
    min_lat: float | None = Query(default=None),
    max_lng: float | None = Query(default=None),
    max_lat: float | None = Query(default=None),
    center_lng: float | None = Query(default=None),
    center_lat: float | None = Query(default=None),
    radius_km: float | None = Query(default=None, gt=0),
    categories: list[Category] | None = Query(default=None),
    audience: list[str] | None = Query(default=None),
    booking_types: list[str] | None = Query(default=None),
    price_min_pence: int | None = Query(default=None, ge=0),
    price_max_pence: int | None = Query(default=None, ge=0),
    cis_min: int | None = Query(default=None, ge=0, le=100),
    cis_max: int | None = Query(default=None, ge=0, le=100),
    include_new_cis: bool = Query(default=True),
    available_from: date | None = Query(default=None),
    available_to: date | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
) -> ListingSearchResponse:
    """Buyer map search — public. Draft/suspended never returned."""
    items, total = listing_service.search_listings(
        min_lng=min_lng,
        min_lat=min_lat,
        max_lng=max_lng,
        max_lat=max_lat,
        center_lng=center_lng,
        center_lat=center_lat,
        radius_km=radius_km,
        categories=categories,
        audience_tags=audience,
        booking_types=booking_types,
        price_min_pence=price_min_pence,
        price_max_pence=price_max_pence,
        cis_min=cis_min,
        cis_max=cis_max,
        include_new_cis=include_new_cis,
        available_from=available_from,
        available_to=available_to,
        page=page,
        page_size=page_size,
    )
    return ListingSearchResponse(
        items=[_to_response(i) for i in items],
        total=total,
        page=page,
        page_size=min(page_size, 20),
    )


@router.get("/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str) -> ListingResponse:
    listing = store.get_listing(listing_id)
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    # Public detail: hide drafts/suspended from anonymous/buyer-facing path
    if listing.status != ListingStatus.PUBLISHED:
        raise HTTPException(status_code=404, detail="Listing not found")
    return _to_response(listing)


@router.post(
    "",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_listing(
    body: ListingCreate,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> ListingResponse:
    listing = listing_service.create_listing_draft(
        user.id, body.model_dump()
    )
    return _to_response(listing)


@router.patch("/{listing_id}", response_model=ListingResponse)
async def update_listing(
    listing_id: str,
    body: ListingUpdate,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> ListingResponse:
    try:
        listing = listing_service.update_listing_draft(
            listing_id, user.id, body.model_dump(exclude_unset=True)
        )
    except ListingServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_response(listing)


@router.post("/{listing_id}/publish", response_model=PublishListingResponse)
async def publish_listing(
    listing_id: str,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> PublishListingResponse:
    try:
        listing = listing_service.publish_listing(listing_id, user.id)
    except ListingServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return PublishListingResponse(
        id=listing.id,
        status=listing.status,
        message="Listing published",
    )
