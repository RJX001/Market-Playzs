"""Booking model — status enum exactly Section 1.3; money in pence."""

from __future__ import annotations

import uuid
from datetime import date
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import BookingStatus
from app.models.sa_enum import pg_enum

if TYPE_CHECKING:
    from app.models.availability import Availability
    from app.models.deliverable import Deliverable
    from app.models.listing import Listing
    from app.models.review import Review
    from app.models.user import User


class Booking(Base, TimestampMixin):
    __tablename__ = "bookings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("listings.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    seller_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    status: Mapped[BookingStatus] = mapped_column(
        pg_enum(BookingStatus, "booking_status"),
        nullable=False,
        default=BookingStatus.Pending_Payment,
        index=True,
    )
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)

    total_amount_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    platform_fee_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    seller_payout_pence: Mapped[int] = mapped_column(Integer, nullable=False)

    stripe_payment_intent_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_charge_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_transfer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    stripe_refund_id: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Per-booking CIS contribution (Section 5.3); set when Completed
    cis_score: Mapped[int | None] = mapped_column(Integer, nullable=True)

    listing: Mapped[Listing] = relationship("Listing", back_populates="bookings")
    buyer: Mapped[User] = relationship(
        "User",
        back_populates="bookings_as_buyer",
        foreign_keys=[buyer_id],
    )
    seller: Mapped[User] = relationship(
        "User",
        back_populates="bookings_as_seller",
        foreign_keys=[seller_id],
    )
    review: Mapped[Review | None] = relationship(
        "Review",
        back_populates="booking",
        uselist=False,
    )
    deliverables: Mapped[list[Deliverable]] = relationship(
        "Deliverable",
        back_populates="booking",
        cascade="all, delete-orphan",
    )
    availability_rows: Mapped[list[Availability]] = relationship(
        "Availability",
        back_populates="booking",
        foreign_keys="Availability.booking_id",
    )
