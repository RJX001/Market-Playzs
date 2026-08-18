"""B8 — buyer and seller dashboard analytics (own-data only)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


class SeriesPoint(BaseModel):
    period: str
    amount_pence: int


class CisTrendPoint(BaseModel):
    period: str
    cis_score: float | None = None


class BuyerCampaignItem(BaseModel):
    booking_id: str
    listing_id: str
    status: str
    total_pence: int
    start_date: date
    end_date: date


class BuyerAnalyticsResponse(BaseModel):
    spend_30d_pence: int
    spend_12m_pence: int
    spend_series_30d: list[SeriesPoint]
    active_campaigns: int
    campaigns: list[BuyerCampaignItem]
    avg_cis_received: float | None = None


class SellerAnalyticsResponse(BaseModel):
    revenue_30d_pence: int
    revenue_12m_series: list[SeriesPoint]
    occupancy_rate: float
    cis_trend: list[CisTrendPoint]
    avg_cis_score: int | None = None
    pending_payouts_pence: int
    active_bookings: int


@router.get(
    "/buyer",
    response_model=BuyerAnalyticsResponse,
    summary="Buyer campaign analytics",
    description=(
        "Authenticated buyer only. Spend over 30 days / 12 months, active "
        "campaigns, and average CIS received — scoped to the caller's bookings."
    ),
)
async def get_buyer_analytics(
    user: CurrentUser = Depends(require_role(UserRole.BUYER)),
) -> BuyerAnalyticsResponse:
    data = analytics_service.buyer_analytics(user.id)
    return BuyerAnalyticsResponse(
        spend_30d_pence=data["spend_30d_pence"],
        spend_12m_pence=data["spend_12m_pence"],
        spend_series_30d=[SeriesPoint(**p) for p in data["spend_series_30d"]],
        active_campaigns=data["active_campaigns"],
        campaigns=[
            BuyerCampaignItem(
                booking_id=c["booking_id"],
                listing_id=c["listing_id"],
                status=c["status"],
                total_pence=c["total_pence"],
                start_date=date.fromisoformat(c["start_date"]),
                end_date=date.fromisoformat(c["end_date"]),
            )
            for c in data["campaigns"]
        ],
        avg_cis_received=data["avg_cis_received"],
    )


@router.get(
    "/seller",
    response_model=SellerAnalyticsResponse,
    summary="Seller revenue analytics",
    description=(
        "Authenticated seller only. Revenue (30-day total + 12-month series), "
        "occupancy rate, CIS trend, and pending payouts for the caller's listings."
    ),
)
async def get_seller_analytics(
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> SellerAnalyticsResponse:
    data = analytics_service.seller_analytics(user.id)
    return SellerAnalyticsResponse(
        revenue_30d_pence=data["revenue_30d_pence"],
        revenue_12m_series=[SeriesPoint(**p) for p in data["revenue_12m_series"]],
        occupancy_rate=data["occupancy_rate"],
        cis_trend=[CisTrendPoint(**p) for p in data["cis_trend"]],
        avg_cis_score=data["avg_cis_score"],
        pending_payouts_pence=data["pending_payouts_pence"],
        active_bookings=data["active_bookings"],
    )
