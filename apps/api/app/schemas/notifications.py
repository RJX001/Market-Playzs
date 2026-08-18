"""Notification request/response schemas (B3)."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class NotificationEventType(str, Enum):
    NEW_BOOKING = "new_booking"
    BOOKING_CANCELLED = "booking_cancelled"
    PAYMENT_RELEASED = "payment_released"
    REVIEW_RECEIVED = "review_received"
    BOOKING_CONFIRMED = "booking_confirmed"
    CAMPAIGN_LIVE = "campaign_live"
    CAMPAIGN_COMPLETE = "campaign_complete"
    REVIEW_REMINDER = "review_reminder"


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    event_type: NotificationEventType
    title: str
    body: str
    booking_id: str | None = None
    listing_id: str | None = None
    read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    unread_count: int


class MarkReadRequest(BaseModel):
    ids: list[str] | None = Field(
        default=None,
        description="Notification ids to mark read. Ignored when mark_all is true.",
    )
    mark_all: bool = Field(
        default=False,
        description="Mark every unread notification for the authenticated user.",
    )


class MarkReadResponse(BaseModel):
    marked_count: int
    unread_count: int
