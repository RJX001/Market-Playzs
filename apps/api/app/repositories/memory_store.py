"""
In-memory repositories for domain APIs.

TODO: Replace with SQLAlchemy ORM + Supabase/PostGIS session once models land.
Do not interpolate user input into raw SQL when swapping.
"""

from __future__ import annotations

import secrets
from copy import deepcopy
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
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
    is_featured: bool = False
    moderation_status: str = "pending"  # pending | approved | rejected
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
class ConversationRecord:
    id: str
    listing_id: str
    buyer_id: str
    seller_id: str
    last_message_preview: str | None = None
    last_message_at: datetime | None = None
    seller_avg_response_seconds: float | None = None
    seller_response_sample_count: int = 0
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass
class MessageRecord:
    id: str
    conversation_id: str
    sender_id: str
    body: str
    flagged: bool = False
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass
class SellerProfile:
    user_id: str
    stripe_account_id: str | None = None
    stripe_charges_enabled: bool = False
    avg_response_seconds: float | None = None
    response_sample_count: int = 0


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


# Dispute first-decision SLA: 72h from creation (under value threshold).
DISPUTE_SLA_HOURS = 72
DISPUTE_SLA_THRESHOLD_PENCE = 50_000  # £500
DEFAULT_ATTRIBUTION_TARGET_URL = "https://marketplays.com"


@dataclass
class PlatformUserRecord:
    id: str
    role: str  # buyer | seller | admin
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass
class SellerVerificationRecord:
    id: str
    seller_id: str
    status: str  # pending | verified | rejected
    business_name: str
    company_number: str | None = None
    notes: str | None = None
    document_urls: list[str] = field(default_factory=list)
    review_reason: str | None = None
    reviewed_by: str | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass
class BuyerProfileRecord:
    user_id: str
    account_type: str  # sme | agency | enterprise
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass
class DisputeRecord:
    id: str
    booking_id: str
    first_decision_due_at: datetime
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)


@dataclass
class AttributionRecord:
    id: str
    booking_id: str
    code: str
    target_url: str = DEFAULT_ATTRIBUTION_TARGET_URL
    scan_count: int = 0
    redemption_count: int = 0
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
        self.conversations: dict[str, ConversationRecord] = {}
        self.messages: dict[str, MessageRecord] = {}
        self.sellers: dict[str, SellerProfile] = {}
        self.audit_logs: list[AuditLogRecord] = []
        self.users: dict[str, PlatformUserRecord] = {}
        self.verifications: dict[str, SellerVerificationRecord] = {}
        self.buyer_profiles: dict[str, BuyerProfileRecord] = {}
        self.disputes: dict[str, DisputeRecord] = {}
        self.attributions_by_booking: dict[str, AttributionRecord] = {}
        self.attributions_by_code: dict[str, AttributionRecord] = {}
        self._seed()

    def _seed(self) -> None:
        """Minimal seed data so search/book flows are demo-runnable."""
        seller_id = "seller-seed-1"
        self.sellers[seller_id] = SellerProfile(
            user_id=seller_id,
            stripe_account_id="acct_seed_connected",
            stripe_charges_enabled=True,
        )
        self.users[seller_id] = PlatformUserRecord(id=seller_id, role="seller")
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
            is_featured=True,
            moderation_status="approved",
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
            self._ensure_attribution_locked(record)
            if record.status == BookingStatus.DISPUTED:
                self._ensure_dispute_locked(record)
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
            previous_status = rec.status
            for key, value in kwargs.items():
                if hasattr(rec, key):
                    setattr(rec, key, value)
            rec.updated_at = _utcnow()
            if (
                rec.status == BookingStatus.DISPUTED
                and previous_status != BookingStatus.DISPUTED
            ):
                self._ensure_dispute_locked(rec)
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

    def list_bookings(self) -> list[BookingRecord]:
        with self._lock:
            return [deepcopy(b) for b in self.bookings.values()]

    def list_bookings_for_buyer(self, buyer_id: str) -> list[BookingRecord]:
        with self._lock:
            return [
                deepcopy(b)
                for b in self.bookings.values()
                if b.buyer_id == buyer_id
            ]

    def list_bookings_for_seller(self, seller_id: str) -> list[BookingRecord]:
        with self._lock:
            return [
                deepcopy(b)
                for b in self.bookings.values()
                if b.seller_id == seller_id
            ]

    def list_availability(self) -> list[AvailabilityRecord]:
        with self._lock:
            return [deepcopy(a) for a in self.availability.values()]

    # --- reviews ---

    def create_review(self, record: ReviewRecord) -> ReviewRecord:
        with self._lock:
            self.reviews[record.id] = record
            return deepcopy(record)

    def list_reviews_for_listing(self, listing_id: str) -> list[ReviewRecord]:
        with self._lock:
            rows = [
                deepcopy(r)
                for r in self.reviews.values()
                if r.listing_id == listing_id
            ]
            return sorted(rows, key=lambda r: r.created_at, reverse=True)

    # --- conversations / messages ---

    def create_conversation(self, record: ConversationRecord) -> ConversationRecord:
        with self._lock:
            self.conversations[record.id] = record
            return deepcopy(record)

    def get_conversation(self, conversation_id: str) -> ConversationRecord | None:
        with self._lock:
            rec = self.conversations.get(conversation_id)
            return deepcopy(rec) if rec else None

    def get_conversation_by_listing_buyer(
        self, listing_id: str, buyer_id: str
    ) -> ConversationRecord | None:
        with self._lock:
            for rec in self.conversations.values():
                if rec.listing_id == listing_id and rec.buyer_id == buyer_id:
                    return deepcopy(rec)
            return None

    def update_conversation(
        self, conversation_id: str, **kwargs: Any
    ) -> ConversationRecord | None:
        with self._lock:
            rec = self.conversations.get(conversation_id)
            if not rec:
                return None
            for key, value in kwargs.items():
                if hasattr(rec, key):
                    setattr(rec, key, value)
            rec.updated_at = _utcnow()
            return deepcopy(rec)

    def list_conversations_for_user(self, user_id: str) -> list[ConversationRecord]:
        with self._lock:
            rows = [
                deepcopy(c)
                for c in self.conversations.values()
                if c.buyer_id == user_id or c.seller_id == user_id
            ]
            return sorted(
                rows,
                key=lambda c: c.last_message_at or c.created_at,
                reverse=True,
            )

    def create_message(self, record: MessageRecord) -> MessageRecord:
        with self._lock:
            self.messages[record.id] = record
            return deepcopy(record)

    def get_message(self, message_id: str) -> MessageRecord | None:
        with self._lock:
            rec = self.messages.get(message_id)
            return deepcopy(rec) if rec else None

    def update_message(self, message_id: str, **kwargs: Any) -> MessageRecord | None:
        with self._lock:
            rec = self.messages.get(message_id)
            if not rec:
                return None
            for key, value in kwargs.items():
                if hasattr(rec, key):
                    setattr(rec, key, value)
            rec.updated_at = _utcnow()
            return deepcopy(rec)

    def list_messages(self, conversation_id: str) -> list[MessageRecord]:
        with self._lock:
            rows = [
                deepcopy(m)
                for m in self.messages.values()
                if m.conversation_id == conversation_id
            ]
            return sorted(rows, key=lambda m: m.created_at)

    def record_seller_response(
        self,
        *,
        conversation_id: str,
        seller_id: str,
        sample_seconds: float,
    ) -> tuple[ConversationRecord | None, SellerProfile]:
        """Update per-thread and seller-wide average response time."""
        with self._lock:
            conv = self.conversations.get(conversation_id)
            if conv:
                n = conv.seller_response_sample_count
                prev = conv.seller_avg_response_seconds or 0.0
                conv.seller_avg_response_seconds = (
                    sample_seconds if n == 0 else (prev * n + sample_seconds) / (n + 1)
                )
                conv.seller_response_sample_count = n + 1
                conv.updated_at = _utcnow()

            profile = self.sellers.get(seller_id)
            if profile is None:
                profile = SellerProfile(user_id=seller_id)
                self.sellers[seller_id] = profile
            sn = profile.response_sample_count
            sprev = profile.avg_response_seconds or 0.0
            profile.avg_response_seconds = (
                sample_seconds if sn == 0 else (sprev * sn + sample_seconds) / (sn + 1)
            )
            profile.response_sample_count = sn + 1
            return deepcopy(conv) if conv else None, deepcopy(profile)

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

    def list_audit_logs(
        self,
        *,
        actor_id: str | None = None,
        action: str | None = None,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> list[AuditLogRecord]:
        with self._lock:
            rows = list(self.audit_logs)
            if actor_id:
                rows = [r for r in rows if r.actor_id == actor_id]
            if action:
                rows = [r for r in rows if r.action == action]
            if entity_type:
                rows = [r for r in rows if r.entity_type == entity_type]
            if entity_id:
                rows = [r for r in rows if r.entity_id == entity_id]
            rows.sort(key=lambda r: r.created_at, reverse=True)
            return [deepcopy(r) for r in rows]

    def list_sellers(self) -> list[SellerProfile]:
        with self._lock:
            return [deepcopy(s) for s in self.sellers.values()]

    def list_users(self) -> list[PlatformUserRecord]:
        with self._lock:
            return [deepcopy(u) for u in self.users.values()]

    def upsert_user(self, record: PlatformUserRecord) -> PlatformUserRecord:
        with self._lock:
            existing = self.users.get(record.id)
            if existing:
                existing.role = record.role
                existing.updated_at = _utcnow()
                return deepcopy(existing)
            self.users[record.id] = record
            return deepcopy(record)

    # --- verification / buyer profile ---

    def get_verification(self, seller_id: str) -> SellerVerificationRecord | None:
        with self._lock:
            rec = self.verifications.get(seller_id)
            return deepcopy(rec) if rec else None

    def upsert_verification(
        self, record: SellerVerificationRecord
    ) -> SellerVerificationRecord:
        with self._lock:
            self.verifications[record.seller_id] = record
            return deepcopy(record)

    def list_verifications(
        self, *, status: str | None = None
    ) -> list[SellerVerificationRecord]:
        with self._lock:
            rows = list(self.verifications.values())
            if status:
                rows = [r for r in rows if r.status == status]
            rows.sort(key=lambda r: r.created_at, reverse=True)
            return [deepcopy(r) for r in rows]

    def get_buyer_profile(self, user_id: str) -> BuyerProfileRecord | None:
        with self._lock:
            rec = self.buyer_profiles.get(user_id)
            return deepcopy(rec) if rec else None

    def upsert_buyer_profile(
        self, record: BuyerProfileRecord
    ) -> BuyerProfileRecord:
        with self._lock:
            self.buyer_profiles[record.user_id] = record
            return deepcopy(record)

    def list_buyer_profiles(self) -> list[BuyerProfileRecord]:
        with self._lock:
            return [deepcopy(p) for p in self.buyer_profiles.values()]

    # --- disputes ---

    def _ensure_dispute_locked(self, booking: BookingRecord) -> DisputeRecord:
        existing = self.disputes.get(booking.id)
        if existing:
            return existing
        now = booking.updated_at if booking.updated_at.tzinfo else _utcnow()
        due = now + timedelta(hours=DISPUTE_SLA_HOURS)
        rec = DisputeRecord(
            id=_new_id(),
            booking_id=booking.id,
            first_decision_due_at=due,
            created_at=now,
            updated_at=now,
        )
        self.disputes[booking.id] = rec
        return rec

    def get_dispute(self, booking_id: str) -> DisputeRecord | None:
        with self._lock:
            rec = self.disputes.get(booking_id)
            return deepcopy(rec) if rec else None

    def list_open_disputes(self) -> list[tuple[BookingRecord, DisputeRecord]]:
        with self._lock:
            rows: list[tuple[BookingRecord, DisputeRecord]] = []
            for booking in self.bookings.values():
                if booking.status != BookingStatus.DISPUTED:
                    continue
                dispute = self._ensure_dispute_locked(booking)
                rows.append((deepcopy(booking), deepcopy(dispute)))
            rows.sort(key=lambda pair: pair[1].first_decision_due_at)
            return rows

    # --- attribution ---

    def _unique_promo_code_locked(self) -> str:
        for _ in range(16):
            code = "MP" + secrets.token_hex(4).upper()
            if code not in self.attributions_by_code:
                return code
        return "MP" + _new_id().replace("-", "")[:10].upper()

    def _ensure_attribution_locked(
        self, booking: BookingRecord
    ) -> AttributionRecord:
        existing = self.attributions_by_booking.get(booking.id)
        if existing:
            return existing
        code = self._unique_promo_code_locked()
        rec = AttributionRecord(
            id=_new_id(),
            booking_id=booking.id,
            code=code,
            target_url=DEFAULT_ATTRIBUTION_TARGET_URL,
        )
        self.attributions_by_booking[booking.id] = rec
        self.attributions_by_code[code] = rec
        return rec

    def get_attribution_for_booking(
        self, booking_id: str
    ) -> AttributionRecord | None:
        with self._lock:
            booking = self.bookings.get(booking_id)
            if not booking:
                return None
            return deepcopy(self._ensure_attribution_locked(booking))

    def get_attribution_by_code(self, code: str) -> AttributionRecord | None:
        with self._lock:
            rec = self.attributions_by_code.get(code)
            return deepcopy(rec) if rec else None

    def record_attribution_scan(self, code: str) -> AttributionRecord | None:
        with self._lock:
            rec = self.attributions_by_code.get(code)
            if not rec:
                return None
            rec.scan_count += 1
            rec.updated_at = _utcnow()
            return deepcopy(rec)

    def reset(self) -> None:
        """Clear all data and re-seed — for tests only."""
        with self._lock:
            self.listings.clear()
            self.availability.clear()
            self.bookings.clear()
            self.reviews.clear()
            self.conversations.clear()
            self.messages.clear()
            self.sellers.clear()
            self.audit_logs.clear()
            self.users.clear()
            self.verifications.clear()
            self.buyer_profiles.clear()
            self.disputes.clear()
            self.attributions_by_booking.clear()
            self.attributions_by_code.clear()
        self._seed()


# Process-wide singleton for runnable stubs
store = MemoryStore()


def new_id() -> str:
    return _new_id()
