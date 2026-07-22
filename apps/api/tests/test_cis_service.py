"""CIS formula tests — Section 5.3."""

from __future__ import annotations

from datetime import date, timedelta

from app.domain_enums import BookingStatus
from app.repositories.memory_store import BookingRecord, new_id, store
from app.services import cis_service


def test_compute_booking_cis_on_time_five_stars() -> None:
    # delivery 1 * 0.5 + (5/5)*0.5 = 1.0 → *100 = 100
    assert cis_service.compute_booking_cis(1.0, 5) == 100.0


def test_compute_booking_cis_late_three_stars() -> None:
    # 0.5 * 0.5 + (3/5)*0.5 = 0.25 + 0.3 = 0.55 → 55
    assert cis_service.compute_booking_cis(0.5, 3) == 55.0


def test_listing_cis_average_and_nullable() -> None:
    listing_id = "listing-seed-1"
    assert store.get_listing(listing_id).cis_score is None

    start = date.today()
    for score in (100.0, 80.0):
        store.create_booking(
            BookingRecord(
                id=new_id(),
                listing_id=listing_id,
                buyer_id="buyer-1",
                seller_id="seller-seed-1",
                status=BookingStatus.COMPLETED,
                start_date=start,
                end_date=start,
                total_pence=2500,
                booking_cis=score,
            )
        )

    result = cis_service.recalculate_listing_cis(listing_id)
    assert result == 90
    assert store.get_listing(listing_id).cis_score == 90


def test_admin_override_sets_flag_and_audit() -> None:
    score = cis_service.apply_admin_override(
        listing_id="listing-seed-1",
        cis_score=42,
        admin_id="admin-1",
        reason="manual adjustment",
    )
    assert score == 42
    listing = store.get_listing("listing-seed-1")
    assert listing is not None
    assert listing.is_cis_overridden is True
    assert listing.cis_score == 42
    assert any(a.action == "cis_override" for a in store.audit_logs)
    # Recalc must not overwrite override
    assert cis_service.recalculate_listing_cis("listing-seed-1") == 42
