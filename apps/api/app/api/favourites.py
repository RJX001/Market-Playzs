"""Saved listings / favourites API (B4)."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, ConfigDict

from app.api.deps import CurrentUser, get_current_user
from app.repositories.memory_store import store
from app.services import favourite_service
from app.services.favourite_service import FavouriteServiceError

router = APIRouter(prefix="/api/favourites", tags=["favourites"])


class FavouriteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: str
    title: str | None = None
    created_at: datetime


class FavouriteListResponse(BaseModel):
    items: list[FavouriteResponse]
    total: int


def _to_response(record) -> FavouriteResponse:
    listing = store.get_listing(record.listing_id)
    return FavouriteResponse(
        id=record.id,
        listing_id=record.listing_id,
        title=listing.title if listing else None,
        created_at=record.created_at,
    )


@router.get(
    "",
    response_model=FavouriteListResponse,
    summary="List saved listings",
    description="Returns the authenticated user's favourited listings, newest first.",
)
async def list_favourites(
    user: CurrentUser = Depends(get_current_user),
) -> FavouriteListResponse:
    rows = favourite_service.list_favourites(user.id)
    return FavouriteListResponse(
        items=[_to_response(row) for row in rows],
        total=len(rows),
    )


@router.post(
    "/{listing_id}",
    response_model=FavouriteResponse,
    summary="Save a listing",
    description=(
        "Add listing_id to the authenticated user's favourites. "
        "Idempotent: returns the existing row if already saved."
    ),
)
async def add_favourite(
    listing_id: str,
    response: Response,
    user: CurrentUser = Depends(get_current_user),
) -> FavouriteResponse:
    try:
        record, created = favourite_service.add_favourite(user.id, listing_id)
    except FavouriteServiceError as exc:
        detail = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if detail == "Listing not found"
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=detail) from exc
    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return _to_response(record)


@router.delete(
    "/{listing_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a saved listing",
    description="Remove listing_id from the authenticated user's favourites.",
)
async def remove_favourite(
    listing_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> None:
    try:
        favourite_service.remove_favourite(user.id, listing_id)
    except FavouriteServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
