"""Listing model — ad spaces with nullable CIS and PostGIS location."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from geoalchemy2 import Geography
from sqlalchemy import Boolean, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import BookingType, ListingCategory, ListingStatus
from app.models.sa_enum import pg_enum

if TYPE_CHECKING:
    from app.models.availability import Availability
    from app.models.booking import Booking
    from app.models.review import Review
    from app.models.user import User


class Listing(Base, TimestampMixin):
    __tablename__ = "listings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[ListingCategory] = mapped_column(
        pg_enum(ListingCategory, "listing_category"),
        nullable=False,
        index=True,
    )
    status: Mapped[ListingStatus] = mapped_column(
        pg_enum(ListingStatus, "listing_status"),
        nullable=False,
        default=ListingStatus.draft,
        index=True,
    )
    booking_type: Mapped[BookingType] = mapped_column(
        pg_enum(BookingType, "booking_type"),
        nullable=False,
        default=BookingType.instant,
    )
    price_per_day_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="GBP")

    # PostGIS geography point (lon/lat WGS84)
    location: Mapped[Any] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )
    address_line1: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True)
    postcode: Mapped[str | None] = mapped_column(String(32), nullable=True)
    audience_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    image_urls: Mapped[list[Any]] = mapped_column(JSONB, nullable=False, default=list)

    # CIS: nullable = "New"; NEVER default to 0 (Section 4)
    cis_score: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    is_cis_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    seller: Mapped[User] = relationship(
        "User",
        back_populates="listings",
        foreign_keys=[seller_id],
    )
    availability_rows: Mapped[list[Availability]] = relationship(
        "Availability",
        back_populates="listing",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="listing",
    )
    reviews: Mapped[list[Review]] = relationship(
        "Review",
        back_populates="listing",
    )
