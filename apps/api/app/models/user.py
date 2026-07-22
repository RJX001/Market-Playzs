"""User model — buyers, sellers, admins. Stripe Connect fields on sellers."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import UserRole
from app.models.sa_enum import pg_enum

if TYPE_CHECKING:
    from app.models.audit_log import AuditLog
    from app.models.booking import Booking
    from app.models.buyer_agent_policy import BuyerAgentPolicy
    from app.models.listing import Listing


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    role: Mapped[UserRole] = mapped_column(
        pg_enum(UserRole, "user_role"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    company_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_suspended: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Stripe Connect (sellers) — Separate Charges and Transfers
    stripe_account_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    stripe_onboarding_complete: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stripe_charges_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stripe_payouts_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    listings: Mapped[list[Listing]] = relationship(
        "Listing",
        back_populates="seller",
        foreign_keys="Listing.seller_id",
    )
    bookings_as_buyer: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="buyer",
        foreign_keys="Booking.buyer_id",
    )
    bookings_as_seller: Mapped[list[Booking]] = relationship(
        "Booking",
        back_populates="seller",
        foreign_keys="Booking.seller_id",
    )
    agent_policy: Mapped[BuyerAgentPolicy | None] = relationship(
        "BuyerAgentPolicy",
        back_populates="buyer",
        uselist=False,
    )
    audit_logs: Mapped[list[AuditLog]] = relationship(
        "AuditLog",
        back_populates="actor",
        foreign_keys="AuditLog.actor_id",
    )
