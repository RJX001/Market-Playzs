"""Seller payout history — GET /api/payments/payouts (own listings only).

Mounted from payments.router so Agent 1 does not need a second include.
If domain_router later includes this module, use prefix="" (not /api/payments)
to avoid duplicating the path.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.services import stripe_service

router = APIRouter()


class PayoutItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    booking_id: str
    listing_id: str
    stripe_transfer_id: str
    amount_pence: int
    commission_pence: int
    total_pence: int
    status: str
    created_at: datetime
    updated_at: datetime


class PayoutListResponse(BaseModel):
    items: list[PayoutItem]


@router.get(
    "/payouts",
    response_model=PayoutListResponse,
    summary="List seller payout history",
    description=(
        "Seller-only. Returns Stripe Connect transfers for bookings on the "
        "authenticated seller's own listings. Amounts are integer pence "
        "(seller share = total minus platform commission). "
        "Transfers are created only after booking Completed "
        "(including dispute approve-seller)."
    ),
)
async def list_payouts(
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> PayoutListResponse:
    rows = stripe_service.list_seller_payouts(user.id)
    return PayoutListResponse(items=[PayoutItem(**row) for row in rows])
