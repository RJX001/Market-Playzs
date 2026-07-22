"""Stripe webhook signature + payments route tests."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.stripe_service import (
    InvalidStripeSignatureError,
    construct_webhook_event,
)


def test_missing_signature_rejected() -> None:
    with pytest.raises(InvalidStripeSignatureError):
        construct_webhook_event(b"{}", None)


def test_invalid_signature_rejected() -> None:
    with pytest.raises(InvalidStripeSignatureError):
        construct_webhook_event(b'{"type":"x"}', "invalid")


def test_webhook_route_returns_400_on_bad_signature() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/payments/webhook",
        content=json.dumps({"type": "payment_intent.succeeded"}),
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "invalid",
        },
    )
    assert response.status_code == 400


def test_webhook_route_accepts_mock_valid_signature() -> None:
    client = TestClient(app)
    payload = {
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_unknown"}},
    }
    response = client.post(
        "/api/payments/webhook",
        content=json.dumps(payload),
        headers={
            "Content-Type": "application/json",
            "Stripe-Signature": "t=1,v1=mock",
        },
    )
    assert response.status_code == 200
