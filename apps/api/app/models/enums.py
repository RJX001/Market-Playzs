"""Shared PostgreSQL / Python enums matching Section 1.3 and schema docs."""

from __future__ import annotations

import enum


class UserRole(str, enum.Enum):
    buyer = "buyer"
    seller = "seller"
    admin = "admin"


class ListingCategory(str, enum.Enum):
    """Exact category values — Section 1.3."""

    sports_club = "sports_club"
    gym = "gym"
    school = "school"
    shop = "shop"
    cafe = "cafe"
    festival = "festival"
    community_event = "community_event"
    billboard = "billboard"
    event_venue = "event_venue"


class ListingStatus(str, enum.Enum):
    draft = "draft"
    published = "published"
    suspended = "suspended"


class BookingType(str, enum.Enum):
    instant = "instant"
    request = "request"


class BookingStatus(str, enum.Enum):
    """Exact booking status values — Section 1.3. Do not invent synonyms."""

    Pending_Payment = "Pending_Payment"
    Confirmed = "Confirmed"
    Live = "Live"
    Awaiting_Proof = "Awaiting_Proof"
    Awaiting_Buyer_Review = "Awaiting_Buyer_Review"
    Completed = "Completed"
    Cancelled = "Cancelled"
    Refunded = "Refunded"
    Disputed = "Disputed"
    Admin_Flagged = "Admin_Flagged"


class DeliverableStatus(str, enum.Enum):
    pending = "pending"
    uploaded = "uploaded"
    verified = "verified"
