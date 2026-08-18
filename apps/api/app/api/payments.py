"""Payments API — Stripe webhook + Connect account link + payout history."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, require_role
from app.api.payouts import router as payouts_router
from app.domain_enums import UserRole
from app.services import booking_service, stripe_service
from app.services.booking_service import (
    BookingServiceError,
    InvalidTransitionError,
)
from app.services.stripe_service import InvalidStripeSignatureError

router = APIRouter(prefix="/api/payments", tags=["payments"])
router.include_router(payouts_router)


class ConnectLinkRequest(BaseModel):
    refresh_url: str = Field(min_length=1)
    return_url: str = Field(min_length=1)


class ConnectLinkResponse(BaseModel):
    url: str
    stripe_account_id: str


@router.post(
    "/webhook",
    status_code=status.HTTP_200_OK,
    summary="Stripe webhook",
    description=(
        "Validates Stripe-Signature against STRIPE_WEBHOOK_SECRET. "
        "Missing or invalid signature → HTTP 400. "
        "Handles payment_intent.succeeded (Pending_Payment → Confirmed, no transfer), "
        "payment_intent.payment_failed (Pending_Payment → Cancelled, release availability), "
        "and transfer.paid (record Connect transfer on the booking). "
        "Unknown events and already-transitioned bookings are acknowledged with 200."
    ),
)
async def stripe_webhook(request: Request) -> dict[str, str]:
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe_service.construct_webhook_event(payload, sig_header)
    except InvalidStripeSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)
        ) from exc

    event_type = event.get("type")
    data_object = (event.get("data") or {}).get("object") or {}

    try:
        if event_type == "payment_intent.succeeded":
            payment_intent_id = data_object.get("id")
            if payment_intent_id:
                booking_service.mark_payment_succeeded(payment_intent_id)
        elif event_type == "payment_intent.payment_failed":
            payment_intent_id = data_object.get("id")
            if payment_intent_id:
                booking_service.mark_payment_failed(payment_intent_id)
        elif event_type == "transfer.paid":
            stripe_service.record_transfer_paid(data_object)
    except (BookingServiceError, InvalidTransitionError):
        # Idempotent: already transitioned or unknown — still 200 to Stripe
        pass

    return {"status": "ok"}


@router.post(
    "/connect/account-link",
    response_model=ConnectLinkResponse,
    summary="Create Stripe Connect onboarding link",
    description=(
        "Seller-only. Creates or reuses an Express connected account (GB) "
        "and returns a Stripe Account Link URL for onboarding. "
        "Response contract: url + stripe_account_id."
    ),
)
async def create_connect_account_link(
    body: ConnectLinkRequest,
    user: CurrentUser = Depends(require_role(UserRole.SELLER)),
) -> ConnectLinkResponse:
    result = stripe_service.create_connect_account_link(
        seller_id=user.id,
        refresh_url=body.refresh_url,
        return_url=body.return_url,
    )
    return ConnectLinkResponse(
        url=result["url"],
        stripe_account_id=result["stripe_account_id"],
    )
