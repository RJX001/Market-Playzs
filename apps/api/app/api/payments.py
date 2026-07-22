"""Payments API — Stripe webhook + Connect account link stub."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.services import booking_service, stripe_service
from app.services.booking_service import (
    BookingServiceError,
    InvalidTransitionError,
)
from app.services.stripe_service import InvalidStripeSignatureError

router = APIRouter(prefix="/api/payments", tags=["payments"])


class ConnectLinkRequest(BaseModel):
    refresh_url: str = Field(min_length=1)
    return_url: str = Field(min_length=1)


class ConnectLinkResponse(BaseModel):
    url: str
    stripe_account_id: str


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request) -> dict[str, str]:
    """
    Stripe webhook — validates Stripe-Signature (400 if invalid).
    Dispatches payment_intent.succeeded / payment_failed into booking_service.
    """
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
    payment_intent_id = data_object.get("id")

    try:
        if event_type == "payment_intent.succeeded" and payment_intent_id:
            booking_service.mark_payment_succeeded(payment_intent_id)
        elif event_type == "payment_intent.payment_failed" and payment_intent_id:
            booking_service.mark_payment_failed(payment_intent_id)
        # Other event types acknowledged but ignored
    except (BookingServiceError, InvalidTransitionError):
        # Idempotent: already transitioned or unknown — still 200 to Stripe
        pass

    return {"status": "ok"}


@router.post("/connect/account-link", response_model=ConnectLinkResponse)
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
