"""Notification stubs (SendGrid wiring TODO)."""

from __future__ import annotations

import logging

from app.domain_enums import BookingStatus
from app.repositories.memory_store import BookingRecord

logger = logging.getLogger(__name__)


def notify_booking_created(booking: BookingRecord) -> None:
    logger.info(
        "notify:booking_created booking_id=%s buyer=%s",
        booking.id,
        booking.buyer_id,
    )


def notify_status_change(
    booking_id: str, status: BookingStatus, *, actor: str
) -> None:
    logger.info(
        "notify:status_change booking_id=%s status=%s actor=%s",
        booking_id,
        status.value,
        actor,
    )


def notify_booking_completed(booking: BookingRecord) -> None:
    logger.info(
        "notify:booking_completed booking_id=%s seller=%s",
        booking.id,
        booking.seller_id,
    )


def notify_listing_published(listing_id: str, seller_id: str) -> None:
    logger.info(
        "notify:listing_published listing_id=%s seller=%s",
        listing_id,
        seller_id,
    )
