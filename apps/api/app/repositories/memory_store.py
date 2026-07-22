"""
In-memory repositories for domain APIs.

TODO: Replace with SQLAlchemy ORM + Supabase/PostGIS session once models land.
Do not interpolate user input into raw SQL when swapping.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from threading import Lock
from typing import Any
from uuid import uuid4

from app.domain_enums import BookingStatus, Category, ListingStatus


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _new_id() -> str:
    return str(uuid4())


@dataclass
class ListingRecord:
    id: str
    seller_id: str
    title: str
    description: str
    category: Category
    status: ListingStatus
    price_per_day_pence: int
    lat: float
    lng: float
    images: list[str] = field(default_factory=list)
    cis_score: int | None = None  # nullable = "New" (never default 0)
    is_cis_overridden: bool = False
    audience_tags: list[str] = field(default_factory=list)
    booking_types: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "seller_id": self.seller_id,
            "title": self.title,
            "description": self.description,
            "category": self.category.value,
            "status": self.status.value,
            "price_per_day_pence": self.price_per_day_pence,
            "lat": self.lat,
            "lng": self.lng,
            "images": list(self.images),
            "cis_score": self.cis_score,
            "is_cis_overridden": self.is_cis_overridden,
            "audience_tags": list(self.audience_tags),
            "booking_types": list(self.booking_types),
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class AvailabilityRecord:
    id: str
    listing_id: str
    day: date
    is_locked: bool = False
    booking_id: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass
class BookingRecord:
    id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    status: BookingStatus
    start_date: date
    end_date: date
    total_pence: int
    commission_pence: int = 0
    stripe_payment_intent_id: str | None = None
    stripe_transfer_id: str | None = None
    delivery_score: float | None = None  # 0 | 0.5 | 1
    rating: int | None = None  # 1–5
    booking_cis: float | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "buyer_id": self.buyer_id,
            "seller_id": self.seller_id,
            "status": self.status.value,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "total_pence": self.total_pence,
            "commission_pence": self.commission_pence,
            "stripe_payment_intent_id": self.stripe_payment_intent_id,
            "stripe_transfer_id": self.stripe_transfer_id,
            "delivery_score": self.delivery_score,
            "rating": self.rating,
            "booking_cis": self.booking_cis,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


@dataclass
class ReviewRecord:
    id: str
    booking_id: str
    listing_id: str
    buyer_id: str
    rating: int
    delivery_score: float
    comment: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass
class SellerProfile:
    user_id: str
    stripe_account_id: str | None = None
    stripe_charges_enabled: bool = False


@dataclass
class AuditLogRecord:
    id: str
    actor_id: str
    action: str
    entity_type: str
    entity_id: str
    details: dict[str, Any] = field(default_factory=dict)
    initiated_by_agent: bool = False
    agent_session_id: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


class MemoryStore:
    """Thread-safe in-memory store. Swap for SQLAlchemy repositories later."""

    def __init__(self) -> None:
        self._lock = Lock()
        self.listings: dict[str, ListingRecord] = {}
        self.availability: dict[str, AvailabilityRecord] = {}
        self.bookings: dict[str, BookingRecord] = {}
        self.reviews: dict[str, ReviewRecord] = {}
        self.sellers: dict[str, SellerProfile] = {}
        self.audit_logs: list[AuditLogRecord] = []
        self._seed()

    def _seed(self) -> None:
        """Minimal seed data so search/book flows are demo-runnable."""
        seller_id = "seller-seed-1"
        self.sellers[seller_id] = SellerProfile(
            user_id=seller_id,
            stripe_account_id="acct_seed_connected",
            stripe_charges_enabled=True,
        )
        listing_id = "listing-seed-1"
        self.listings[listing_id] = ListingRecord(
            id=listing_id,
            seller_id=seller_id,
            title="Seed Billboard — Shoreditch",
            description="Demo published listing for map search.",
            category=Category.BILLBOARD,
            status=ListingStatus.PUBLISHED,
            price_per_day_pence=2500,
            lat=51.5255,
            lng=-0.0815,
            images=["https://example.com/seed-billboard.webp"],
            cis_score=None,
            audience_tags=["local"],
            booking_types=["instant"],
        )
        today = date.today()
        for offset in range(14):
            day = date.fromordinal(today.toordinal() + offset)
            avail_id = _new_id()
            self.availability[avail_id] = AvailabilityRecord(
                id=avail_id,
                listing_id=listing_id,
                day=day,
                is_locked=False,
            )

    # --- listings ---

    def create_listing(self, record: ListingRecord) -> ListingRecord:
        with self._lock:
            self.listings[record.id] = record
            return deepcopy(record)

    def get_listing(self, listing_id: str) -> ListingRecord | None:
        with self._lock:
            rec = self.listings.get(listing_id)
            return deepcopy(rec) if rec else None

    def update_listing(self, listing_id: str, **kwargs: Any) -> ListingRecord | None:
        with self._lock:
            rec = self.listings.get(listing_id)
            if not rec:
                return None
            for key, value in kwargs.items():
                if hasattr(rec, key):
                    setattr(rec, key, value)
            rec.updated_at = _utcnow()
            return deepcopy(rec)

    def list_listings(self) -> list[ListingRecord]:
        with self._lock:
            return [deepcopy(r) for r in self.listings.values()]

    # --- availability ---

    def get_availability_for_range(
        self, listing_id: str, start: date, end: date
    ) -> list[AvailabilityRecord]:
        with self._lock:
            rows = [
                deepcopy(a)
                for a in self.availability.values()
                if a.listing_id == listing_id and start <= a.day <= end
            ]
            return sorted(rows, key=lambda a: a.day)

    def lock_availability(
        self, listing_id: str, start: date, end: date, booking_id: str
    ) -> list[AvailabilityRecord]:
        with self._lock:
            locked: list[AvailabilityRecord] = []
            for a in self.availability.values():
                if a.listing_id == listing_id and start <= a.day <= end:
                    if a.is_locked:
                        raise ValueError(f"Date {a.day.isoformat()} already locked")
                    a.is_locked = True
                    a.booking_id = booking_id
                    a.updated_at = _utcnow()
                    locked.append(deepcopy(a))
            if not locked:
                raise ValueError("No availability rows in requested range")
            expected_days = (end - start).days + 1
            if len(locked) != expected_days:
                # rollback locks for this booking
                for a in self.availability.values():
                    if a.booking_id == booking_id:
                        a.is_locked = False
                        a.booking_id = None
                        a.updated_at = _utcnow()
                raise ValueError("Not all dates available in range")
            return locked

    def unlock_availability(self, booking_id: str) -> None:
        with self._lock:
            for a in self.availability.values():
                if a.booking_id == booking_id:
                    a.is_locked = False
                    a.booking_id = None
                    a.updated_at = _utcnow()

    def ensure_availability_window(
        self, listing_id: str, start: date, end: date
    ) -> None:
        """Create missing unlocked rows for dates in range (seller stub helper)."""
        with self._lock:
            existing = {
                a.day
                for a in self.availability.values()
                if a.listing_id == listing_id and start <= a.day <= end
            }
            cursor = start
            while cursor <= end:
                if cursor not in existing:
                    aid = _new_id()
                    self.availability[aid] = AvailabilityRecord(
                        id=aid, listing_id=listing_id, day=cursor
                    )
                cursor = date.fromordinal(cursor.toordinal() + 1)

    # --- bookings ---

    def create_booking(self, record: BookingRecord) -> BookingRecord:
        with self._lock:
            self.bookings[record.id] = record
            return deepcopy(record)

    def get_booking(self, booking_id: str) -> BookingRecord | None:
        with self._lock:
            rec = self.bookings.get(booking_id)
            return deepcopy(rec) if rec else None

    def get_booking_by_payment_intent(
        self, payment_intent_id: str
    ) -> BookingRecord | None:
        with self._lock:
            for b in self.bookings.values():
                if b.stripe_payment_intent_id == payment_intent_id:
                    return deepcopy(b)
            return None

    def update_booking(self, booking_id: str, **kwargs: Any) -> BookingRecord | None:
        with self._lock:
            rec = self.bookings.get(booking_id)
            if not rec:
                return None
            for key, value in kwargs.items():
                if hasattr(rec, key):
                    setattr(rec, key, value)
            rec.updated_at = _utcnow()
            return deepcopy(rec)

    def list_bookings_for_listing(self, listing_id: str) -> list[BookingRecord]:
        with self._lock:
            return [
                deepcopy(b)
                for b in self.bookings.values()
                if b.listing_id == listing_id
            ]

    def list_completed_bookings_for_listing(
        self, listing_id: str
    ) -> list[BookingRecord]:
        with self._lock:
            return [
                deepcopy(b)
                for b in self.bookings.values()
                if b.listing_id == listing_id
                and b.status == BookingStatus.COMPLETED
                and b.booking_cis is not None
            ]

    # --- reviews ---

    def create_review(self, record: ReviewRecord) -> ReviewRecord:
        with self._lock:
            self.reviews[record.id] = record
            return deepcopy(record)

    # --- sellers / audit ---

    def get_seller(self, user_id: str) -> SellerProfile | None:
        with self._lock:
            s = self.sellers.get(user_id)
            return deepcopy(s) if s else None

    def upsert_seller(self, profile: SellerProfile) -> SellerProfile:
        with self._lock:
            self.sellers[profile.user_id] = profile
            return deepcopy(profile)

    def add_audit_log(self, record: AuditLogRecord) -> AuditLogRecord:
        with self._lock:
            self.audit_logs.append(record)
            return deepcopy(record)

    def reset(self) -> None:
        """Clear all data and re-seed — for tests only."""
        with self._lock:
            self.listings.clear()
            self.availability.clear()
            self.bookings.clear()
            self.reviews.clear()
            self.sellers.clear()
            self.audit_logs.clear()
        self._seed()


# Process-wide singleton for runnable stubs
store = MemoryStore()


def new_id() -> str:
    return _new_id()
