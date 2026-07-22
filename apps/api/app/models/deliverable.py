"""Deliverable (proof) model — status pending|uploaded|verified."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin
from app.models.enums import DeliverableStatus
from app.models.sa_enum import pg_enum

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.user import User


class Deliverable(Base, TimestampMixin):
    __tablename__ = "deliverables"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[DeliverableStatus] = mapped_column(
        pg_enum(DeliverableStatus, "deliverable_status"),
        nullable=False,
        default=DeliverableStatus.pending,
        index=True,
    )
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uploaded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    verified_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    booking: Mapped[Booking] = relationship("Booking", back_populates="deliverables")
    verified_by: Mapped[User | None] = relationship("User", foreign_keys=[verified_by_id])
