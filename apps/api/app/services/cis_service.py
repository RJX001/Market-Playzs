"""CIS formula (Section 5.3) — score is per listing, nullable.

delivery_component = delivery_score * 0.5     # 0 | 0.5 | 1
rating_component   = (rating / 5) * 0.5       # rating 1–5
new_booking_cis    = (delivery_component + rating_component) * 100
listing_cis        = AVG(booking_cis) across Completed bookings, rounded
"""

from __future__ import annotations

from app.domain_enums import DELIVERY_SCORES, BookingStatus
from app.repositories.memory_store import (
    AuditLogRecord,
    new_id,
    store,
)


class CisServiceError(ValueError):
    pass


def compute_booking_cis(delivery_score: float, rating: int) -> float:
    if delivery_score not in DELIVERY_SCORES:
        raise CisServiceError("delivery_score must be exactly 0, 0.5, or 1")
    if rating < 1 or rating > 5:
        raise CisServiceError("rating must be 1–5")

    delivery_component = delivery_score * 0.5
    rating_component = (rating / 5) * 0.5
    return round((delivery_component + rating_component) * 100, 10)


def recalculate_listing_cis(listing_id: str) -> int | None:
    """
    Average booking CIS across Completed bookings for the listing.

    Returns None if no completed scored bookings (listing stays "New").
    Skips overwrite when is_cis_overridden is True unless force via admin path.
    """
    listing = store.get_listing(listing_id)
    if not listing:
        raise CisServiceError(f"Listing {listing_id} not found")

    if listing.is_cis_overridden:
        return listing.cis_score

    completed = store.list_completed_bookings_for_listing(listing_id)
    if not completed:
        store.update_listing(listing_id, cis_score=None)
        return None

    avg = sum(b.booking_cis or 0.0 for b in completed) / len(completed)
    score = int(round(avg))
    store.update_listing(listing_id, cis_score=score)
    return score


def apply_admin_override(
    *,
    listing_id: str,
    cis_score: int,
    admin_id: str,
    reason: str,
) -> int:
    """
    Admin CIS override — sets is_cis_overridden and writes audit_logs.
    An override without an audit log entry is a bug (Section 4 / 8).
    """
    if cis_score < 0 or cis_score > 100:
        raise CisServiceError("cis_score must be 0–100")

    listing = store.get_listing(listing_id)
    if not listing:
        raise CisServiceError(f"Listing {listing_id} not found")

    store.update_listing(
        listing_id, cis_score=cis_score, is_cis_overridden=True
    )
    store.add_audit_log(
        AuditLogRecord(
            id=new_id(),
            actor_id=admin_id,
            action="cis_override",
            entity_type="listing",
            entity_id=listing_id,
            details={
                "cis_score": cis_score,
                "previous_cis_score": listing.cis_score,
                "reason": reason,
            },
            initiated_by_agent=False,
        )
    )
    return cis_score


def get_listing_cis(listing_id: str) -> tuple[int | None, bool, int]:
    listing = store.get_listing(listing_id)
    if not listing:
        raise CisServiceError(f"Listing {listing_id} not found")
    completed = [
        b
        for b in store.list_bookings_for_listing(listing_id)
        if b.status == BookingStatus.COMPLETED and b.booking_cis is not None
    ]
    return listing.cis_score, listing.is_cis_overridden, len(completed)
