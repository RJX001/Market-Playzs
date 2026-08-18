"""Admin domain schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

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


class ModerationRejectRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=2000)


class ModerationListingItem(BaseModel):
    id: str
    seller_id: str
    title: str
    category: str
    status: str
    moderation_status: str
    created_at: datetime
    updated_at: datetime


class ModerationQueueResponse(BaseModel):
    items: list[ModerationListingItem]


class AuditLogItem(BaseModel):
    id: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any]
    initiated_by_agent: bool
    agent_session_id: str | None
    created_at: datetime


class AuditLogListResponse(BaseModel):
    items: list[AuditLogItem]
    total: int
    page: int
    page_size: int


class DisputeListItem(BaseModel):
    booking_id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    status: str
    total_pence: int
    commission_pence: int
    first_decision_due_at: datetime
    under_value_threshold: bool
    created_at: datetime
    updated_at: datetime


class DisputeListResponse(BaseModel):
    items: list[DisputeListItem]


class AdminReportResponse(BaseModel):
    users: int
    sellers: int
    buyers: int
    listings: int
    bookings: int
    gmv_pence: int
    gmv_30d_pence: int
    revenue_pence: int
    commission_pence: int
