"""B9 — unauthenticated marketplace headline stats (in-memory cache 60s)."""

from __future__ import annotations

import time
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel

from app.services import analytics_service

router = APIRouter(prefix="/api/public", tags=["public"])

_CACHE_TTL_SECONDS = 60.0
_cache_expires_at: float = 0.0
_cache_payload: dict[str, Any] | None = None


class CategoryCount(BaseModel):
    category: str
    count: int


class FeaturedListing(BaseModel):
    id: str
    title: str
    category: str
    cis_score: int | None
    lat: float
    lng: float
    price_per_day_pence: int


class PublicStatsResponse(BaseModel):
    listing_count: int
    categories: list[CategoryCount]
    featured: list[FeaturedListing]


def clear_cache() -> None:
    """Test helper — drop the 60s in-memory cache."""
    global _cache_expires_at, _cache_payload
    _cache_expires_at = 0.0
    _cache_payload = None


def _get_cached() -> dict[str, Any]:
    global _cache_expires_at, _cache_payload
    now = time.monotonic()
    if _cache_payload is not None and now < _cache_expires_at:
        return _cache_payload
    payload = analytics_service.public_stats()
    _cache_payload = payload
    _cache_expires_at = now + _CACHE_TTL_SECONDS
    return payload


@router.get(
    "/stats",
    response_model=PublicStatsResponse,
    summary="Public marketplace statistics",
    description=(
        "Unauthenticated. Published listing count, category breakdown, and "
        "featured listings (minimal fields). Cached in-memory for 60 seconds."
    ),
)
async def get_public_stats() -> PublicStatsResponse:
    data = _get_cached()
    return PublicStatsResponse(
        listing_count=data["listing_count"],
        categories=[CategoryCount(**c) for c in data["categories"]],
        featured=[FeaturedListing(**f) for f in data["featured"]],
    )
