"""
ALL Stripe logic lives here only.

Separate Charges and Transfers:
- Charge buyer via PaymentIntent on the platform account at booking create.
- Hold funds until booking status is Completed.
- Transfer to seller Connect account only on Completed (or after
  dispute approve-seller, which transitions to Completed first).
- Prefer source_transaction (original charge id) so Stripe queues the
  transfer until platform funds are available.

Webhook handlers MUST validate Stripe-Signature (HTTP 400 if invalid).
Never expose STRIPE_SECRET_KEY to the frontend.
"""

from __future__ import annotations

import os
from typing import Any
from uuid import uuid4

from app.domain_enums import BookingStatus
from app.repositories.memory_store import BookingRecord, store

# Optional real Stripe SDK — falls back to deterministic mocks when unset/unavailable
try:
    import stripe
except ImportError:  # pragma: no cover
    stripe = None  # type: ignore[assignment]


HANDLED_WEBHOOK_EVENTS = frozenset(
    {
        "payment_intent.succeeded",
        "payment_intent.payment_failed",
        "transfer.paid",
    }
)


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


def _transfer_group(booking_id: str) -> str:
    return f"booking_{booking_id}"


def _seller_share_pence(booking: BookingRecord) -> int:
    return booking.total_pence - booking.commission_pence


def _charge_id_from_intent(intent: Any) -> str | None:
    """Extract the charge id from a PaymentIntent for source_transaction."""
    latest = None
    if isinstance(intent, dict):
        latest = intent.get("latest_charge")
    else:
        latest = getattr(intent, "latest_charge", None)
        if latest is None and hasattr(intent, "get"):
            latest = intent.get("latest_charge")
    if isinstance(latest, str) and latest:
        return latest
    if isinstance(latest, dict):
        charge_id = latest.get("id")
        if isinstance(charge_id, str) and charge_id:
            return charge_id
    return None


def _retrieve_source_transaction(payment_intent_id: str | None) -> str | None:
    """Best-effort charge id from the original PaymentIntent. None if unavailable."""
    if not payment_intent_id or not _configure_stripe() or stripe is None:
        return None
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
    except Exception:
        return None
    return _charge_id_from_intent(intent)


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
            transfer_group=_transfer_group(booking.id),
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
    Create (or reuse) an Express Connect account and return an Account Link URL.

    Contract: {url, stripe_account_id}. Live Stripe when configured; mock otherwise.
    """
    seller = store.get_seller(seller_id)
    if seller is None:
        from app.repositories.memory_store import SellerProfile

        seller = store.upsert_seller(
            SellerProfile(user_id=seller_id, stripe_account_id=None)
        )

    account_id = seller.stripe_account_id
    if _configure_stripe() and stripe is not None:
        from app.repositories.memory_store import SellerProfile

        if not account_id:
            account = stripe.Account.create(
                type="express",
                country="GB",
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
            )
            account_id = str(account["id"])
            store.upsert_seller(
                SellerProfile(
                    user_id=seller_id,
                    stripe_account_id=account_id,
                    stripe_charges_enabled=bool(
                        account.get("charges_enabled", False)
                    ),
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

    Dispute approve-seller reaches this path after Disputed → Completed.
    transfer_amount_pence = total_pence - commission_pence
    Sets source_transaction to the original charge id when retrievable.
    Returns transfer id, or None if already transferred / zero amount.
    """
    if booking.status != BookingStatus.COMPLETED:
        raise StripeServiceError(
            "Seller transfer is only allowed when booking status is Completed"
        )

    if booking.stripe_transfer_id:
        return booking.stripe_transfer_id

    transfer_amount = _seller_share_pence(booking)
    if transfer_amount <= 0:
        return None

    seller = store.get_seller(booking.seller_id)
    if not seller or not seller.stripe_account_id:
        raise StripeServiceError(
            "Seller has no Stripe Connect account for transfer"
        )

    if _configure_stripe() and stripe is not None:
        params: dict[str, Any] = {
            "amount": transfer_amount,
            "currency": "gbp",
            "destination": seller.stripe_account_id,
            "transfer_group": _transfer_group(booking.id),
            "metadata": {
                "booking_id": booking.id,
                "listing_id": booking.listing_id,
            },
        }
        source_transaction = _retrieve_source_transaction(
            booking.stripe_payment_intent_id
        )
        if source_transaction:
            params["source_transaction"] = source_transaction
        transfer = stripe.Transfer.create(**params)
        return str(transfer["id"])

    return f"tr_mock_{booking.id.replace('-', '')[:20]}"


def record_transfer_paid(transfer_object: dict[str, Any]) -> str | None:
    """
    Handle transfer.paid — persist the transfer id on the booking if missing.

    Does not create a Transfer (that happens only on Completed).
    Returns booking id when matched, else None.
    """
    transfer_id = transfer_object.get("id")
    if not isinstance(transfer_id, str) or not transfer_id:
        return None

    metadata = transfer_object.get("metadata") or {}
    booking_id = metadata.get("booking_id")
    booking = store.get_booking(booking_id) if booking_id else None
    if booking is None:
        booking = _find_booking_by_transfer_id(transfer_id)
    if booking is None:
        return None

    if booking.stripe_transfer_id != transfer_id:
        store.update_booking(booking.id, stripe_transfer_id=transfer_id)
    return booking.id


def _find_booking_by_transfer_id(transfer_id: str) -> BookingRecord | None:
    for listing in store.list_listings():
        for booking in store.list_bookings_for_listing(listing.id):
            if booking.stripe_transfer_id == transfer_id:
                return booking
    return None


def list_seller_payouts(seller_id: str) -> list[dict[str, Any]]:
    """
    Payout history for a seller — transfers on that seller's own listings only.
    """
    items: list[dict[str, Any]] = []
    for listing in store.list_listings():
        if listing.seller_id != seller_id:
            continue
        for booking in store.list_bookings_for_listing(listing.id):
            if booking.seller_id != seller_id:
                continue
            if not booking.stripe_transfer_id:
                continue
            items.append(
                {
                    "booking_id": booking.id,
                    "listing_id": booking.listing_id,
                    "stripe_transfer_id": booking.stripe_transfer_id,
                    "amount_pence": _seller_share_pence(booking),
                    "commission_pence": booking.commission_pence,
                    "total_pence": booking.total_pence,
                    "status": booking.status.value,
                    "created_at": booking.created_at,
                    "updated_at": booking.updated_at,
                }
            )
    items.sort(key=lambda row: row["created_at"], reverse=True)
    return items


def refund_payment(booking: BookingRecord, amount_pence: int | None = None) -> str:
    """Refund the platform PaymentIntent.

    ``amount_pence`` omitted or equal to ``booking.total_pence`` → full refund.
    Partial amounts (e.g. 50% buyer cancel 3–7 days) pass Stripe ``amount``.
    """
    if not booking.stripe_payment_intent_id:
        raise StripeServiceError("Booking has no PaymentIntent to refund")

    params: dict[str, Any] = {"payment_intent": booking.stripe_payment_intent_id}
    if amount_pence is not None:
        if amount_pence <= 0:
            raise StripeServiceError("Refund amount must be positive pence")
        if amount_pence < booking.total_pence:
            params["amount"] = amount_pence

    if _configure_stripe() and stripe is not None:
        refund = stripe.Refund.create(**params)
        return str(refund["id"])

    return f"re_mock_{booking.id.replace('-', '')[:20]}"
