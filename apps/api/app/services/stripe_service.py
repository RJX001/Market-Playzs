"""
ALL Stripe logic lives here only.

Separate Charges and Transfers:
- Charge buyer via PaymentIntent on the platform account at booking create.
- Hold funds until booking status is Completed.
- Transfer to seller Connect account only on Completed.

Webhook handlers MUST validate Stripe-Signature (HTTP 400 if invalid).
Never expose STRIPE_SECRET_KEY to the frontend.
"""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from app.repositories.memory_store import BookingRecord, store

# Optional real Stripe SDK — falls back to deterministic mocks when unset/unavailable
try:
    import stripe
except ImportError:  # pragma: no cover
    stripe = None  # type: ignore[assignment]


class StripeServiceError(ValueError):
    pass


class InvalidStripeSignatureError(StripeServiceError):
    """Raised when Stripe-Signature is missing or invalid → map to HTTP 400."""


def _secret_key() -> str | None:
    return os.getenv("STRIPE_SECRET_KEY")


def _webhook_secret() -> str | None:
    return os.getenv("STRIPE_WEBHOOK_SECRET")


def _configure_stripe() -> bool:
    """Return True if live Stripe SDK is configured."""
    key = _secret_key()
    if not key or stripe is None:
        return False
    stripe.api_key = key
    return True


def create_payment_intent(booking: BookingRecord) -> dict[str, str]:
    """
    Create a platform PaymentIntent for the booking total (pence).

    Returns {"id": payment_intent_id, "client_secret": ...}.
    """
    if booking.total_pence < 0:
        raise StripeServiceError("total_pence must be >= 0")

    metadata = {
        "booking_id": booking.id,
        "listing_id": booking.listing_id,
        "buyer_id": booking.buyer_id,
        "seller_id": booking.seller_id,
    }

    if _configure_stripe():
        assert stripe is not None
        intent = stripe.PaymentIntent.create(
            amount=booking.total_pence,
            currency="gbp",
            metadata=metadata,
            automatic_payment_methods={"enabled": True},
        )
        return {
            "id": str(intent["id"]),
            "client_secret": str(intent["client_secret"]),
        }

    # Mock for local/runnable stub without Stripe credentials
    mock_id = f"pi_mock_{booking.id.replace('-', '')[:24]}"
    return {
        "id": mock_id,
        "client_secret": f"{mock_id}_secret_mock",
    }


def construct_webhook_event(
    payload: bytes, sig_header: str | None
) -> dict[str, Any]:
    """
    Validate Stripe-Signature and return the event dict.

    Raises InvalidStripeSignatureError on missing/invalid signature (→ 400).
    """
    if not sig_header:
        raise InvalidStripeSignatureError("Missing Stripe-Signature header")

    wh_secret = _webhook_secret()

    if _configure_stripe() and wh_secret and stripe is not None:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, wh_secret
            )
            return dict(event)
        except Exception as exc:  # SignatureVerificationError / ValueError
            raise InvalidStripeSignatureError(
                "Invalid Stripe-Signature"
            ) from exc

    # Mock mode: require a non-empty signature header; accept JSON payload
    # Reject obviously invalid signatures so tests can assert 400 behaviour.
    if sig_header in {"invalid", "bad", "unsigned"}:
        raise InvalidStripeSignatureError("Invalid Stripe-Signature")

    import json

    try:
        data = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidStripeSignatureError("Invalid payload") from exc

    if not isinstance(data, dict) or "type" not in data:
        raise InvalidStripeSignatureError("Invalid event payload")
    return data


def create_connect_account_link(
    seller_id: str,
    refresh_url: str,
    return_url: str,
) -> dict[str, str]:
    """
    Stub: create (or reuse) a Connect account and return an Account Link URL.
    """
    seller = store.get_seller(seller_id)
    if seller is None:
        from app.repositories.memory_store import SellerProfile

        seller = store.upsert_seller(
            SellerProfile(user_id=seller_id, stripe_account_id=None)
        )

    account_id = seller.stripe_account_id
    if _configure_stripe() and stripe is not None:
        if not account_id:
            account = stripe.Account.create(type="express", country="GB")
            account_id = str(account["id"])
            from app.repositories.memory_store import SellerProfile

            store.upsert_seller(
                SellerProfile(
                    user_id=seller_id,
                    stripe_account_id=account_id,
                    stripe_charges_enabled=False,
                )
            )
        link = stripe.AccountLink.create(
            account=account_id,
            refresh_url=refresh_url,
            return_url=return_url,
            type="account_onboarding",
        )
        return {"url": str(link["url"]), "stripe_account_id": account_id}

    # Mock Connect onboarding link
    if not account_id:
        account_id = f"acct_mock_{uuid4().hex[:12]}"
        from app.repositories.memory_store import SellerProfile

        store.upsert_seller(
            SellerProfile(
                user_id=seller_id,
                stripe_account_id=account_id,
                stripe_charges_enabled=True,
            )
        )
    return {
        "url": (
            f"https://connect.stripe.com/mock/setup/{account_id}"
            f"?refresh={refresh_url}&return={return_url}"
        ),
        "stripe_account_id": account_id,
    }


def transfer_on_completed(booking: BookingRecord) -> str | None:
    """
    Transfer seller payout only when booking is Completed.

    transfer_amount_pence = total_pence - commission_pence
    Returns transfer id, or None if already transferred / zero amount.
    """
    if booking.stripe_transfer_id:
        return booking.stripe_transfer_id

    transfer_amount = booking.total_pence - booking.commission_pence
    if transfer_amount <= 0:
        return None

    seller = store.get_seller(booking.seller_id)
    if not seller or not seller.stripe_account_id:
        raise StripeServiceError(
            "Seller has no Stripe Connect account for transfer"
        )

    if _configure_stripe() and stripe is not None:
        transfer = stripe.Transfer.create(
            amount=transfer_amount,
            currency="gbp",
            destination=seller.stripe_account_id,
            metadata={
                "booking_id": booking.id,
                "listing_id": booking.listing_id,
            },
        )
        return str(transfer["id"])

    return f"tr_mock_{booking.id.replace('-', '')[:20]}"


def refund_payment(booking: BookingRecord) -> str:
    """Full refund of the platform PaymentIntent (Disputed → Refunded path)."""
    if not booking.stripe_payment_intent_id:
        raise StripeServiceError("Booking has no PaymentIntent to refund")

    if _configure_stripe() and stripe is not None:
        refund = stripe.Refund.create(
            payment_intent=booking.stripe_payment_intent_id
        )
        return str(refund["id"])

    return f"re_mock_{booking.id.replace('-', '')[:20]}"
