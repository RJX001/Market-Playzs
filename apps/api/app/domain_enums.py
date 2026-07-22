"""Shared domain enums — exact values from Section 1.3 / 5.2."""

from __future__ import annotations

from enum import Enum


class BookingStatus(str, Enum):
    PENDING_PAYMENT = "Pending_Payment"
    CONFIRMED = "Confirmed"
    LIVE = "Live"
    AWAITING_PROOF = "Awaiting_Proof"
    AWAITING_BUYER_REVIEW = "Awaiting_Buyer_Review"
    COMPLETED = "Completed"
    CANCELLED = "Cancelled"
    REFUNDED = "Refunded"
    DISPUTED = "Disputed"
    ADMIN_FLAGGED = "Admin_Flagged"


class ListingStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    SUSPENDED = "suspended"


class Category(str, Enum):
    SPORTS_CLUB = "sports_club"
    GYM = "gym"
    SCHOOL = "school"
    SHOP = "shop"
    CAFE = "cafe"
    FESTIVAL = "festival"
    COMMUNITY_EVENT = "community_event"
    BILLBOARD = "billboard"
    EVENT_VENUE = "event_venue"


class UserRole(str, Enum):
    BUYER = "buyer"
    SELLER = "seller"
    ADMIN = "admin"


class DeliverableStatus(str, Enum):
    PENDING = "pending"
    UPLOADED = "uploaded"
    VERIFIED = "verified"


# delivery_score is exactly one of 0, 0.5, 1 (Section 4)
DELIVERY_SCORES: frozenset[float] = frozenset({0.0, 0.5, 1.0})

# Terminal booking statuses — no further transitions (Section 5.2)
TERMINAL_BOOKING_STATUSES: frozenset[BookingStatus] = frozenset(
    {
        BookingStatus.COMPLETED,
        BookingStatus.CANCELLED,
        BookingStatus.REFUNDED,
    }
)

# Authoritative valid transitions (Section 5.2)
VALID_TRANSITIONS: dict[BookingStatus, frozenset[BookingStatus]] = {
    BookingStatus.PENDING_PAYMENT: frozenset(
        {BookingStatus.CONFIRMED, BookingStatus.CANCELLED}
    ),
    BookingStatus.CONFIRMED: frozenset(
        {BookingStatus.LIVE, BookingStatus.CANCELLED}
    ),
    BookingStatus.LIVE: frozenset(
        {BookingStatus.AWAITING_PROOF, BookingStatus.DISPUTED}
    ),
    BookingStatus.AWAITING_PROOF: frozenset(
        {BookingStatus.AWAITING_BUYER_REVIEW, BookingStatus.ADMIN_FLAGGED}
    ),
    BookingStatus.AWAITING_BUYER_REVIEW: frozenset(
        {BookingStatus.COMPLETED, BookingStatus.DISPUTED}
    ),
    BookingStatus.DISPUTED: frozenset(
        {BookingStatus.COMPLETED, BookingStatus.REFUNDED}
    ),
    BookingStatus.ADMIN_FLAGGED: frozenset(),  # admin tooling may extend later
    BookingStatus.COMPLETED: frozenset(),
    BookingStatus.CANCELLED: frozenset(),
    BookingStatus.REFUNDED: frozenset(),
}
