"""In-app notifications + transactional email (B3).

Email is always logged. SendGrid is used only when SENDGRID_API_KEY is set.
Heavy sends go through FastAPI BackgroundTasks (or a daemon thread when no
request-scoped tasks object is available) so request handlers never block.
"""

from __future__ import annotations

import logging
import os
import threading
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

import httpx
from fastapi import BackgroundTasks

from app.domain_enums import BookingStatus
from app.repositories.memory_store import BookingRecord, store as domain_store
from app.schemas.notifications import NotificationEventType

logger = logging.getLogger(__name__)

SENDGRID_MAIL_URL = "https://api.sendgrid.com/v3/mail/send"
DEFAULT_FROM_EMAIL = "notifications@marketplays.com"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class NotificationRecord:
    id: str
    user_id: str
    event_type: NotificationEventType
    title: str
    body: str
    booking_id: str | None = None
    listing_id: str | None = None
    recipient_email: str | None = None
    read: bool = False
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "event_type": self.event_type,
            "title": self.title,
            "body": self.body,
            "booking_id": self.booking_id,
            "listing_id": self.listing_id,
            "read": self.read,
            "created_at": self.created_at,
        }


class NotificationStore:
    """Thread-safe per-user in-app notifications."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._items: dict[str, NotificationRecord] = {}

    def reset(self) -> None:
        with self._lock:
            self._items.clear()

    def add(self, record: NotificationRecord) -> NotificationRecord:
        with self._lock:
            self._items[record.id] = record
            return deepcopy(record)

    def list_for_user(self, user_id: str) -> list[NotificationRecord]:
        with self._lock:
            rows = [
                deepcopy(r) for r in self._items.values() if r.user_id == user_id
            ]
        return sorted(rows, key=lambda r: r.created_at, reverse=True)

    def unread_count(self, user_id: str) -> int:
        with self._lock:
            return sum(
                1
                for r in self._items.values()
                if r.user_id == user_id and not r.read
            )

    def mark_read(self, user_id: str, ids: list[str] | None, *, mark_all: bool) -> int:
        marked = 0
        id_set = set(ids or [])
        with self._lock:
            for rec in self._items.values():
                if rec.user_id != user_id or rec.read:
                    continue
                if mark_all or rec.id in id_set:
                    rec.read = True
                    marked += 1
        return marked

    def has_unread_event(
        self,
        user_id: str,
        event_type: NotificationEventType,
        booking_id: str,
    ) -> bool:
        with self._lock:
            return any(
                r.user_id == user_id
                and r.event_type == event_type
                and r.booking_id == booking_id
                and not r.read
                for r in self._items.values()
            )


_store = NotificationStore()
_email_log: list[dict[str, Any]] = []
_email_log_lock = Lock()


def reset_store() -> None:
    _store.reset()
    with _email_log_lock:
        _email_log.clear()


def get_email_log() -> list[dict[str, Any]]:
    with _email_log_lock:
        return list(_email_log)


def list_notifications(
    user_id: str, *, page: int = 1, page_size: int = 20
) -> tuple[list[NotificationRecord], int, int]:
    page_size = min(max(page_size, 1), 50)
    page = max(page, 1)
    rows = _store.list_for_user(user_id)
    total = len(rows)
    start = (page - 1) * page_size
    unread = _store.unread_count(user_id)
    return rows[start : start + page_size], total, unread


def unread_count(user_id: str) -> int:
    return _store.unread_count(user_id)


def mark_read(
    user_id: str, ids: list[str] | None, *, mark_all: bool
) -> tuple[int, int]:
    marked = _store.mark_read(user_id, ids, mark_all=mark_all)
    return marked, _store.unread_count(user_id)


def _listing_title(listing_id: str | None) -> str:
    if not listing_id:
        return "your listing"
    listing = domain_store.get_listing(listing_id)
    if listing is None:
        return "your listing"
    return listing.title


def _resolve_email(user_id: str, explicit: str | None) -> str | None:
    if explicit and "@" in explicit:
        return explicit
    if "@" in user_id:
        return user_id
    return None


def deliver_email(
    to_email: str | None,
    subject: str,
    body: str,
    event_type: str,
    notification_id: str,
) -> None:
    """Log the email, then optionally POST to SendGrid. Never raises."""
    entry = {
        "to_email": to_email,
        "subject": subject,
        "body": body,
        "event_type": event_type,
        "notification_id": notification_id,
    }
    with _email_log_lock:
        _email_log.append(entry)
    logger.info(
        "email:event=%s notification_id=%s to=%s subject=%s",
        event_type,
        notification_id,
        to_email or "(none)",
        subject,
    )
    api_key = os.getenv("SENDGRID_API_KEY", "").strip()
    if not api_key or not to_email:
        return
    from_email = os.getenv("SENDGRID_FROM_EMAIL", DEFAULT_FROM_EMAIL).strip()
    try:
        response = httpx.post(
            SENDGRID_MAIL_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "personalizations": [{"to": [{"email": to_email}]}],
                "from": {"email": from_email},
                "subject": subject,
                "content": [{"type": "text/plain", "value": body}],
            },
            timeout=10.0,
        )
        if response.status_code >= 400:
            logger.warning(
                "sendgrid failed status=%s notification_id=%s body=%s",
                response.status_code,
                notification_id,
                response.text[:500],
            )
    except Exception:
        logger.exception(
            "sendgrid send failed notification_id=%s", notification_id
        )


def _in_pytest() -> bool:
    return os.getenv("PYTEST_CURRENT_TEST") is not None


def _schedule_email(
    background_tasks: BackgroundTasks | None,
    *,
    to_email: str | None,
    subject: str,
    body: str,
    event_type: str,
    notification_id: str,
) -> None:
    args = (to_email, subject, body, event_type, notification_id)
    if background_tasks is not None:
        background_tasks.add_task(deliver_email, *args)
        return
    if _in_pytest():
        deliver_email(*args)
        return
    thread = threading.Thread(target=deliver_email, args=args, daemon=True)
    thread.start()


def _emit(
    *,
    user_id: str,
    event_type: NotificationEventType,
    title: str,
    body: str,
    booking_id: str | None = None,
    listing_id: str | None = None,
    recipient_email: str | None = None,
    background_tasks: BackgroundTasks | None = None,
) -> NotificationRecord:
    record = NotificationRecord(
        id=str(uuid4()),
        user_id=user_id,
        event_type=event_type,
        title=title,
        body=body,
        booking_id=booking_id,
        listing_id=listing_id,
        recipient_email=_resolve_email(user_id, recipient_email),
        read=False,
    )
    created = _store.add(record)
    _schedule_email(
        background_tasks,
        to_email=created.recipient_email,
        subject=title,
        body=body,
        event_type=event_type.value,
        notification_id=created.id,
    )
    return created


def notify_new_booking(
    booking: BookingRecord,
    *,
    background_tasks: BackgroundTasks | None = None,
    seller_email: str | None = None,
) -> NotificationRecord:
    title_name = _listing_title(booking.listing_id)
    return _emit(
        user_id=booking.seller_id,
        event_type=NotificationEventType.NEW_BOOKING,
        title="New booking",
        body=f"You have a new booking on {title_name}.",
        booking_id=booking.id,
        listing_id=booking.listing_id,
        recipient_email=seller_email,
        background_tasks=background_tasks,
    )


def notify_booking_cancelled(
    booking: BookingRecord,
    *,
    background_tasks: BackgroundTasks | None = None,
    seller_email: str | None = None,
) -> NotificationRecord:
    title_name = _listing_title(booking.listing_id)
    return _emit(
        user_id=booking.seller_id,
        event_type=NotificationEventType.BOOKING_CANCELLED,
        title="Booking cancelled",
        body=f"A booking for {title_name} was cancelled.",
        booking_id=booking.id,
        listing_id=booking.listing_id,
        recipient_email=seller_email,
        background_tasks=background_tasks,
    )


def notify_payment_released(
    booking: BookingRecord,
    *,
    background_tasks: BackgroundTasks | None = None,
    seller_email: str | None = None,
) -> NotificationRecord:
    title_name = _listing_title(booking.listing_id)
    return _emit(
        user_id=booking.seller_id,
        event_type=NotificationEventType.PAYMENT_RELEASED,
        title="Payment released",
        body=f"Payment has been released for {title_name}.",
        booking_id=booking.id,
        listing_id=booking.listing_id,
        recipient_email=seller_email,
        background_tasks=background_tasks,
    )


def notify_review_received(
    booking: BookingRecord,
    *,
    background_tasks: BackgroundTasks | None = None,
    seller_email: str | None = None,
) -> NotificationRecord:
    title_name = _listing_title(booking.listing_id)
    return _emit(
        user_id=booking.seller_id,
        event_type=NotificationEventType.REVIEW_RECEIVED,
        title="Review received",
        body=f"You received a new review on {title_name}.",
        booking_id=booking.id,
        listing_id=booking.listing_id,
        recipient_email=seller_email,
        background_tasks=background_tasks,
    )


def notify_booking_confirmed(
    booking: BookingRecord,
    *,
    background_tasks: BackgroundTasks | None = None,
    buyer_email: str | None = None,
) -> NotificationRecord:
    title_name = _listing_title(booking.listing_id)
    return _emit(
        user_id=booking.buyer_id,
        event_type=NotificationEventType.BOOKING_CONFIRMED,
        title="Booking confirmed",
        body=f"Your booking for {title_name} is confirmed.",
        booking_id=booking.id,
        listing_id=booking.listing_id,
        recipient_email=buyer_email,
        background_tasks=background_tasks,
    )


def notify_campaign_live(
    booking: BookingRecord,
    *,
    background_tasks: BackgroundTasks | None = None,
    buyer_email: str | None = None,
) -> NotificationRecord:
    title_name = _listing_title(booking.listing_id)
    return _emit(
        user_id=booking.buyer_id,
        event_type=NotificationEventType.CAMPAIGN_LIVE,
        title="Campaign live",
        body=f"Your campaign at {title_name} is now live.",
        booking_id=booking.id,
        listing_id=booking.listing_id,
        recipient_email=buyer_email,
        background_tasks=background_tasks,
    )


def notify_campaign_complete(
    booking: BookingRecord,
    *,
    background_tasks: BackgroundTasks | None = None,
    buyer_email: str | None = None,
) -> NotificationRecord:
    title_name = _listing_title(booking.listing_id)
    return _emit(
        user_id=booking.buyer_id,
        event_type=NotificationEventType.CAMPAIGN_COMPLETE,
        title="Campaign complete",
        body=f"Your campaign at {title_name} is complete.",
        booking_id=booking.id,
        listing_id=booking.listing_id,
        recipient_email=buyer_email,
        background_tasks=background_tasks,
    )


def notify_review_reminder(
    booking: BookingRecord,
    *,
    background_tasks: BackgroundTasks | None = None,
    buyer_email: str | None = None,
) -> NotificationRecord | None:
    """Buyer review reminder. Skips if an unread reminder already exists."""
    if _store.has_unread_event(
        booking.buyer_id,
        NotificationEventType.REVIEW_REMINDER,
        booking.id,
    ):
        return None
    title_name = _listing_title(booking.listing_id)
    return _emit(
        user_id=booking.buyer_id,
        event_type=NotificationEventType.REVIEW_REMINDER,
        title="Review reminder",
        body=f"Please review your campaign at {title_name}.",
        booking_id=booking.id,
        listing_id=booking.listing_id,
        recipient_email=buyer_email,
        background_tasks=background_tasks,
    )


def emit_review_reminders(
    *,
    background_tasks: BackgroundTasks | None = None,
) -> int:
    """Scan Awaiting_Buyer_Review bookings and emit buyer review reminders."""
    emitted = 0
    for booking in list(domain_store.bookings.values()):
        if booking.status != BookingStatus.AWAITING_BUYER_REVIEW:
            continue
        if notify_review_reminder(booking, background_tasks=background_tasks):
            emitted += 1
    return emitted


def notify_booking_created(booking: BookingRecord) -> None:
    logger.info(
        "notify:booking_created booking_id=%s buyer=%s",
        booking.id,
        booking.buyer_id,
    )
    notify_new_booking(booking)


def notify_status_change(
    booking_id: str, status: BookingStatus, *, actor: str
) -> None:
    logger.info(
        "notify:status_change booking_id=%s status=%s actor=%s",
        booking_id,
        status.value,
        actor,
    )
    booking = domain_store.get_booking(booking_id)
    if booking is None:
        return
    if status == BookingStatus.CONFIRMED:
        notify_booking_confirmed(booking)
    elif status == BookingStatus.LIVE:
        notify_campaign_live(booking)
    elif status == BookingStatus.CANCELLED:
        notify_booking_cancelled(booking)
    elif status == BookingStatus.AWAITING_BUYER_REVIEW:
        notify_review_reminder(booking)


def notify_booking_completed(booking: BookingRecord) -> None:
    logger.info(
        "notify:booking_completed booking_id=%s seller=%s",
        booking.id,
        booking.seller_id,
    )
    notify_payment_released(booking)
    notify_campaign_complete(booking)
    if booking.rating is not None:
        notify_review_received(booking)


def notify_listing_published(listing_id: str, seller_id: str) -> None:
    logger.info(
        "notify:listing_published listing_id=%s seller=%s",
        listing_id,
        seller_id,
    )
