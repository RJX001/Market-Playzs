"""Cancellation refund policy — integer pence only.

Buyer cancel (calendar days until campaign ``start_date``):
  >7 days  → 100%
  3–7 days → 50%
  <3 days  → 0%
Seller cancel → 100% regardless of notice.

Stripe charge/refund execution stays in ``stripe_service`` (payments workstream).
This module only computes the policy amount.
"""

from __future__ import annotations

from datetime import date
from typing import Literal

CancelActor = Literal["buyer", "seller"]


def days_until_start(start_date: date, *, today: date | None = None) -> int:
    today = today or date.today()
    return (start_date - today).days


def refund_percent(
    *,
    cancelled_by: CancelActor,
    start_date: date,
    today: date | None = None,
) -> int:
    if cancelled_by == "seller":
        return 100
    days = days_until_start(start_date, today=today)
    if days > 7:
        return 100
    if days >= 3:
        return 50
    return 0


def calculate_refund_pence(
    *,
    total_pence: int,
    cancelled_by: CancelActor,
    start_date: date,
    today: date | None = None,
) -> tuple[int, int]:
    """Return ``(refund_pence, refund_percent)`` using integer pence."""
    if total_pence < 0:
        raise ValueError("total_pence must be >= 0")
    percent = refund_percent(
        cancelled_by=cancelled_by, start_date=start_date, today=today
    )
    refund_pence = int(round(total_pence * percent / 100))
    return refund_pence, percent
