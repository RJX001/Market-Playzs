"""Admin domain schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class DisputeResolution(str, Enum):
    APPROVE_SELLER = "approve_seller"
    FULL_REFUND = "full_refund"
    PARTIAL_REFUND = "partial_refund"


class DisputeResolveRequest(BaseModel):
    resolution: DisputeResolution
    partial_percent: int | None = Field(
        default=None,
        ge=1,
        le=99,
        description="Required when resolution is partial_refund",
    )
    reason: str = Field(min_length=1, max_length=2000)


class DisputeResolveResponse(BaseModel):
    booking_id: str
    status: str
    message: str


class SuspendListingRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)
