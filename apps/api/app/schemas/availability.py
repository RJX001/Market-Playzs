"""Availability schemas — one row per date per listing."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class AvailabilityDay(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: str
    day: date
    is_locked: bool
    booking_id: str | None
    created_at: datetime
    updated_at: datetime


class AvailabilityQueryResponse(BaseModel):
    listing_id: str
    start_date: date
    end_date: date
    days: list[AvailabilityDay]


class AvailabilityWindowCreate(BaseModel):
    start_date: date
    end_date: date = Field(description="Inclusive end date")
