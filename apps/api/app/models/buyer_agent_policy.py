"""Buyer agent spend policies (Section 9.4) — money in pence."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class BuyerAgentPolicy(Base, TimestampMixin):
    __tablename__ = "buyer_agent_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    max_per_booking_value_pence: Mapped[int] = mapped_column(Integer, nullable=False)
    max_monthly_agent_spend_pence: Mapped[int] = mapped_column(Integer, nullable=False)

    buyer: Mapped[User] = relationship("User", back_populates="agent_policy")
