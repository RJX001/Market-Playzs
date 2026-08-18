"""Listings API — search, CRUD stubs, publish guard."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.api.deps import CurrentUser, require_role
from app.domain_enums import Category, UserRole
from app.schemas.listings import (
    ListingCreate,
    ListingResponse,
    ListingSearchResponse,
    ListingUpdate,
    PublishListingResponse,
)
from app.services import auth_service, listing_service
from app.services.listing_service import (
    ListingForbiddenError,
    ListingNotFoundError,
    ListingServiceError,
)

router = APIRouter(prefix="/api/listings", tags=["listings"])
_optional_bearer = HTTPBearer(auto_error=False)


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


def _http_for_listing_error(exc: ListingServiceError) -> HTTPException:
    if isinstance(exc, ListingNotFoundError):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, ListingForbiddenError):
        return HTTPException(status_code=403, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


def _requester_id(
    credentials: HTTPAuthorizationCredentials | None,
) -> str | None:
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = auth_service.decode_access_token(credentials.credentials)
        return str(payload["sub"])
    except (auth_service.AuthError, KeyError, ValueError):
        return None


def _merge_list(*groups: list | None) -> list | None:
    merged: list = []
    seen: set = set()
    for group in groups:
        if not group:
            continue
        for item in group:
            if item in seen:
                continue
            seen.add(item)
            merged.append(item)
    return merged or None


@router.get(
    "",
    response_model=ListingSearchResponse,
    summary="Search published listings",
    description=(
        "Buyer map search. Draft and suspended listings are never returned. "
        "Filters AND across types and OR within multi-selects. Canonical query "
        "names are preserved; aliases (category, lat/lng/radius, price_min/max, "
        "date_from/to, booking_type, sort) are also accepted."
    ),
)
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
    # Additive aliases — do not replace canonical names above
    category: list[Category] | None = Query(default=None),
    lat: float | None = Query(default=None, ge=-90, le=90),
    lng: float | None = Query(default=None, ge=-180, le=180),
    radius: float | None = Query(default=None, gt=0),
    price_min: int | None = Query(default=None, ge=0),
    price_max: int | None = Query(default=None, ge=0),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    booking_type: list[str] | None = Query(default=None),
    sort: str | None = Query(
        default=None,
        description="newest | price_asc | price_desc | cis_asc | cis_desc | distance",
    ),
) -> ListingSearchResponse:
    """Buyer map search — public. Draft/suspended never returned."""
    try:
        items, total = listing_service.search_listings(
            min_lng=min_lng,
            min_lat=min_lat,
            max_lng=max_lng,
            max_lat=max_lat,
            center_lng=center_lng if center_lng is not None else lng,
            center_lat=center_lat if center_lat is not None else lat,
            radius_km=radius_km if radius_km is not None else radius,
            categories=_merge_list(categories, category),
            audience_tags=audience,
            booking_types=_merge_list(booking_types, booking_type),
            price_min_pence=(
                price_min_pence if price_min_pence is not None else price_min
            ),
            price_max_pence=(
                price_max_pence if price_max_pence is not None else price_max
            ),
            cis_min=cis_min,
            cis_max=cis_max,
            include_new_cis=include_new_cis,
            available_from=(
                available_from if available_from is not None else date_from
            ),
            available_to=available_to if available_to is not None else date_to,
            sort=sort,
            page=page,
            page_size=page_size,
        )
    except ListingServiceError as exc:
        raise _http_for_listing_error(exc) from exc
    return ListingSearchResponse(
        items=[_to_response(i) for i in items],
        total=total,
        page=page,
        page_size=min(page_size, 20),
    )


@router.get(
    "/mine",
    response_model=ListingSearchResponse,
    summary="List the authenticated seller's listings",
    description=(
        "Seller inventory including draft and suspended rows. "
        "Must be declared before /{listing_id} so 'mine' is not treated as an id."
    ),
)
async def list_my_listings(
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> ListingSearchResponse:
    items = listing_service.list_seller_listings(user.id)
    return ListingSearchResponse(
        items=[_to_response(i) for i in items],
        total=len(items),
        page=1,
        page_size=len(items),
    )


@router.get(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Get a listing",
    description=(
        "Public detail returns published listings only. Draft and suspended "
        "listings 404 for buyers; the owning seller may still retrieve them."
    ),
)
async def get_listing(
    listing_id: str,
    credentials: HTTPAuthorizationCredentials | None = Depends(_optional_bearer),
) -> ListingResponse:
    try:
        listing = listing_service.get_listing_for_viewer(
            listing_id, _requester_id(credentials)
        )
    except ListingServiceError as exc:
        raise _http_for_listing_error(exc) from exc
    return _to_response(listing)


@router.post(
    "",
    response_model=ListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a listing draft",
    description="Seller-only. New listings start as draft until publish succeeds.",
)
async def create_listing(
    body: ListingCreate,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> ListingResponse:
    listing = listing_service.create_listing_draft(
        user.id, body.model_dump()
    )
    return _to_response(listing)


@router.patch(
    "/{listing_id}",
    response_model=ListingResponse,
    summary="Update a listing draft",
    description="Seller-only. Ownership is required. Suspended listings cannot be edited.",
)
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
        raise _http_for_listing_error(exc) from exc
    return _to_response(listing)


@router.post(
    "/{listing_id}/publish",
    response_model=PublishListingResponse,
    summary="Publish a listing",
    description=(
        "Seller-only publish guard: connected Stripe account with charges enabled, "
        "required fields complete, and at least one image. Ownership is required."
    ),
)
async def publish_listing(
    listing_id: str,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> PublishListingResponse:
    try:
        listing = listing_service.publish_listing(listing_id, user.id)
    except ListingServiceError as exc:
        raise _http_for_listing_error(exc) from exc
    return PublishListingResponse(
        id=listing.id,
        status=listing.status,
        message="Listing published",
    )
