"""CIS schemas — score is per listing and nullable."""

from __future__ import annotations

from pydantic import BaseModel, Field


class CisScoreResponse(BaseModel):
    listing_id: str
    cis_score: int | None = Field(
        description="Nullable integer; null means New listing, never treat as 0"
    )
    is_cis_overridden: bool
    completed_bookings_counted: int


class CisOverrideRequest(BaseModel):
    cis_score: int = Field(ge=0, le=100)
    reason: str = Field(min_length=1, max_length=1000)
