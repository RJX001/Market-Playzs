"""Read-only aggregates for buyer/seller dashboards, public stats, admin report.

GMV = booking value before commission (paid / in-flight bookings).
Revenue = commission earned + featured + subscriptions (featured/subs = 0 until billed).
Money stays integer pence.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime, timedelta, timezone

from app.domain_enums import BookingStatus, ListingStatus
from app.repositories.memory_store import (
    DISPUTE_SLA_THRESHOLD_PENCE,
    BookingRecord,
    store,
)

# Paid / committed bookings count toward GMV (exclude abandoned + refunded).
GMV_STATUSES: frozenset[BookingStatus] = frozenset(
    {
        BookingStatus.CONFIRMED,
        BookingStatus.LIVE,
        BookingStatus.AWAITING_PROOF,
        BookingStatus.AWAITING_BUYER_REVIEW,
        BookingStatus.COMPLETED,
        BookingStatus.DISPUTED,
        BookingStatus.ADMIN_FLAGGED,
    }
)

ACTIVE_CAMPAIGN_STATUSES: frozenset[BookingStatus] = frozenset(
    {
        BookingStatus.CONFIRMED,
        BookingStatus.LIVE,
        BookingStatus.AWAITING_PROOF,
        BookingStatus.AWAITING_BUYER_REVIEW,
    }
)

PENDING_PAYOUT_STATUSES: frozenset[BookingStatus] = frozenset(
    {
        BookingStatus.CONFIRMED,
        BookingStatus.LIVE,
        BookingStatus.AWAITING_PROOF,
        BookingStatus.AWAITING_BUYER_REVIEW,
        BookingStatus.DISPUTED,
    }
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _month_key(dt: datetime) -> str:
    return _as_utc(dt).strftime("%Y-%m")


def _day_key(dt: datetime) -> str:
    return _as_utc(dt).date().isoformat()


def _in_last_days(dt: datetime, days: int, *, now: datetime | None = None) -> bool:
    now = now or _utcnow()
    return _as_utc(dt) >= now - timedelta(days=days)


def _seller_share(booking: BookingRecord) -> int:
    return max(booking.total_pence - booking.commission_pence, 0)


def buyer_analytics(buyer_id: str) -> dict:
    """Own-data only: spend, campaigns, average CIS received."""
    now = _utcnow()
    bookings = store.list_bookings_for_buyer(buyer_id)
    paid = [b for b in bookings if b.status in GMV_STATUSES]

    spend_30d = sum(
        b.total_pence for b in paid if _in_last_days(b.created_at, 30, now=now)
    )
    spend_12m = sum(
        b.total_pence for b in paid if _in_last_days(b.created_at, 365, now=now)
    )

    daily: dict[str, int] = defaultdict(int)
    for b in paid:
        if _in_last_days(b.created_at, 30, now=now):
            daily[_day_key(b.created_at)] += b.total_pence
    spend_series = []
    for offset in range(29, -1, -1):
        day = (now.date() - timedelta(days=offset)).isoformat()
        spend_series.append({"period": day, "amount_pence": daily.get(day, 0)})

    campaigns = [
        {
            "booking_id": b.id,
            "listing_id": b.listing_id,
            "status": b.status.value,
            "total_pence": b.total_pence,
            "start_date": b.start_date.isoformat(),
            "end_date": b.end_date.isoformat(),
        }
        for b in bookings
        if b.status in ACTIVE_CAMPAIGN_STATUSES
    ]

    cis_values = [b.booking_cis for b in paid if b.booking_cis is not None]
    avg_cis = round(sum(cis_values) / len(cis_values), 2) if cis_values else None

    return {
        "spend_30d_pence": spend_30d,
        "spend_12m_pence": spend_12m,
        "spend_series_30d": spend_series,
        "active_campaigns": len(campaigns),
        "campaigns": campaigns,
        "avg_cis_received": avg_cis,
    }


def seller_analytics(seller_id: str) -> dict:
    """Own-data only: revenue, occupancy, CIS trend, pending payouts."""
    now = _utcnow()
    bookings = store.list_bookings_for_seller(seller_id)
    completed = [b for b in bookings if b.status == BookingStatus.COMPLETED]

    revenue_30d = sum(
        _seller_share(b)
        for b in completed
        if _in_last_days(b.updated_at, 30, now=now)
    )

    monthly: dict[str, int] = defaultdict(int)
    for b in completed:
        if _in_last_days(b.updated_at, 365, now=now):
            monthly[_month_key(b.updated_at)] += _seller_share(b)

    revenue_12m = []
    cursor = date(now.year, now.month, 1)
    for _ in range(11, -1, -1):
        key = cursor.strftime("%Y-%m")
        revenue_12m.append(
            {"period": key, "amount_pence": monthly.get(key, 0)}
        )
        if cursor.month == 1:
            cursor = date(cursor.year - 1, 12, 1)
        else:
            cursor = date(cursor.year, cursor.month - 1, 1)
    revenue_12m.reverse()

    occupancy = _occupancy_rate(seller_id, now.date())

    cis_by_month: dict[str, list[float]] = defaultdict(list)
    for b in completed:
        if b.booking_cis is None:
            continue
        if _in_last_days(b.updated_at, 365, now=now):
            cis_by_month[_month_key(b.updated_at)].append(b.booking_cis)
    cis_trend = []
    cursor = date(now.year, now.month, 1)
    months: list[date] = []
    for _ in range(12):
        months.append(cursor)
        if cursor.month == 1:
            cursor = date(cursor.year - 1, 12, 1)
        else:
            cursor = date(cursor.year, cursor.month - 1, 1)
    months.reverse()
    for month in months:
        key = month.strftime("%Y-%m")
        values = cis_by_month.get(key, [])
        cis_trend.append(
            {
                "period": key,
                "cis_score": round(sum(values) / len(values), 2) if values else None,
            }
        )

    pending = [b for b in bookings if b.status in PENDING_PAYOUT_STATUSES]
    pending_payouts_pence = sum(_seller_share(b) for b in pending)

    listing_scores = [
        listing.cis_score
        for listing in store.list_listings()
        if listing.seller_id == seller_id and listing.cis_score is not None
    ]
    avg_cis = (
        int(round(sum(listing_scores) / len(listing_scores)))
        if listing_scores
        else None
    )

    return {
        "revenue_30d_pence": revenue_30d,
        "revenue_12m_series": revenue_12m,
        "occupancy_rate": occupancy,
        "cis_trend": cis_trend,
        "avg_cis_score": avg_cis,
        "pending_payouts_pence": pending_payouts_pence,
        "active_bookings": len(
            [b for b in bookings if b.status in ACTIVE_CAMPAIGN_STATUSES]
        ),
    }


def _occupancy_rate(seller_id: str, today: date) -> float:
    listing_ids = {
        listing.id
        for listing in store.list_listings()
        if listing.seller_id == seller_id
    }
    if not listing_ids:
        return 0.0
    window_end = today + timedelta(days=29)
    rows = [
        row
        for row in store.list_availability()
        if row.listing_id in listing_ids and today <= row.day <= window_end
    ]
    if not rows:
        return 0.0
    locked = sum(1 for row in rows if row.is_locked)
    return round(locked / len(rows), 4)


def public_stats() -> dict:
    """Unauthenticated headline metrics + featured listings (minimal fields)."""
    listings = [
        listing
        for listing in store.list_listings()
        if listing.status == ListingStatus.PUBLISHED
    ]
    category_counts: dict[str, int] = defaultdict(int)
    for listing in listings:
        category_counts[listing.category.value] += 1
    featured = [
        {
            "id": listing.id,
            "title": listing.title,
            "category": listing.category.value,
            "cis_score": listing.cis_score,
            "lat": listing.lat,
            "lng": listing.lng,
            "price_per_day_pence": listing.price_per_day_pence,
        }
        for listing in listings
        if listing.is_featured
    ]
    return {
        "listing_count": len(listings),
        "categories": [
            {"category": key, "count": category_counts[key]}
            for key in sorted(category_counts)
        ],
        "featured": featured,
    }


def admin_report() -> dict:
    """Platform KPIs. GMV = booking value before commission."""
    now = _utcnow()
    bookings = store.list_bookings()
    listings = store.list_listings()
    sellers = store.list_sellers()
    users = store.list_users()
    buyer_profiles = store.list_buyer_profiles()

    seller_ids = {s.user_id for s in sellers}
    buyer_ids = {b.buyer_id for b in bookings} | {p.user_id for p in buyer_profiles}
    user_ids = {u.id for u in users} | seller_ids | buyer_ids

    paid = [b for b in bookings if b.status in GMV_STATUSES]
    gmv = sum(b.total_pence for b in paid)
    gmv_30d = sum(
        b.total_pence for b in paid if _in_last_days(b.created_at, 30, now=now)
    )
    completed = [b for b in bookings if b.status == BookingStatus.COMPLETED]
    commission = sum(b.commission_pence for b in completed)
    # Featured listing fees + subscriptions are not billed yet.
    revenue = commission

    return {
        "users": len(user_ids),
        "sellers": len(seller_ids),
        "buyers": len(buyer_ids),
        "listings": len(listings),
        "bookings": len(bookings),
        "gmv_pence": gmv,
        "gmv_30d_pence": gmv_30d,
        "revenue_pence": revenue,
        "commission_pence": commission,
    }


def dispute_under_threshold(total_pence: int) -> bool:
    return total_pence <= DISPUTE_SLA_THRESHOLD_PENCE
