"""Saved searches API — persist listing filter JSON (B5)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.api.deps import CurrentUser, get_current_user
from app.services import saved_search_service
from app.services.saved_search_service import SavedSearchServiceError

router = APIRouter(prefix="/api/saved-searches", tags=["saved-searches"])


class SavedSearchCreate(BaseModel):
    name: str | None = Field(default=None, max_length=200)
    filters: dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "Listing search filter combination (category, radius, audience, "
            "price, dates, CIS min, booking type, sort, etc.)."
        ),
    )


class SavedSearchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    filters: dict[str, Any]
    created_at: datetime


class SavedSearchListResponse(BaseModel):
    items: list[SavedSearchResponse]
    total: int


def _to_response(record) -> SavedSearchResponse:
    return SavedSearchResponse(
        id=record.id,
        name=record.name,
        filters=record.filters,
        created_at=record.created_at,
    )


@router.get(
    "",
    response_model=SavedSearchListResponse,
    summary="List saved searches",
    description="Returns the authenticated user's saved listing-filter combinations.",
)
async def list_saved_searches(
    user: CurrentUser = Depends(get_current_user),
) -> SavedSearchListResponse:
    rows = saved_search_service.list_saved_searches(user.id)
    return SavedSearchListResponse(
        items=[_to_response(row) for row in rows],
        total=len(rows),
    )


@router.post(
    "",
    response_model=SavedSearchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save a search",
    description="Store a listing filter JSON blob for the authenticated user.",
)
async def create_saved_search(
    body: SavedSearchCreate,
    user: CurrentUser = Depends(get_current_user),
) -> SavedSearchResponse:
    try:
        record = saved_search_service.create_saved_search(
            user.id, name=body.name, filters=body.filters
        )
    except SavedSearchServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc
    return _to_response(record)


@router.delete(
    "/{search_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a saved search",
    description="Delete a saved search owned by the authenticated user.",
)
async def delete_saved_search(
    search_id: str,
    user: CurrentUser = Depends(get_current_user),
) -> None:
    try:
        saved_search_service.delete_saved_search(user.id, search_id)
    except SavedSearchServiceError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
