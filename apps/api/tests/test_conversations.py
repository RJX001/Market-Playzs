"""Conversations / messages API — ownership, leakage flag, seller response time."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.conversations import router as conversations_router
from app.api.deps import CurrentUser, get_current_user
from app.domain_enums import UserRole
from app.repositories.memory_store import store
from app.services import conversation_service
from app.services.conversation_service import ConversationServiceError


BUYER_ID = "buyer-1"
SELLER_ID = "seller-seed-1"
OTHER_BUYER_ID = "buyer-2"
LISTING_ID = "listing-seed-1"


def _client_as(user_id: str, role: UserRole) -> TestClient:
    app = FastAPI()
    app.include_router(conversations_router)

    async def _override() -> CurrentUser:
        return CurrentUser(id=user_id, role=role, email=f"{user_id}@example.com")

    app.dependency_overrides[get_current_user] = _override
    return TestClient(app)


def _open_thread(buyer_id: str = BUYER_ID) -> str:
    conv, created = conversation_service.create_conversation(
        listing_id=LISTING_ID,
        actor_id=buyer_id,
        actor_role=UserRole.BUYER,
    )
    assert created is True
    return conv.id


def test_create_conversation_buyer_and_idempotent() -> None:
    conv, created = conversation_service.create_conversation(
        listing_id=LISTING_ID,
        actor_id=BUYER_ID,
        actor_role=UserRole.BUYER,
    )
    assert created is True
    assert conv.buyer_id == BUYER_ID
    assert conv.seller_id == SELLER_ID
    again, created_again = conversation_service.create_conversation(
        listing_id=LISTING_ID,
        actor_id=BUYER_ID,
        actor_role=UserRole.BUYER,
    )
    assert created_again is False
    assert again.id == conv.id


def test_create_conversation_seller_requires_buyer_id() -> None:
    try:
        conversation_service.create_conversation(
            listing_id=LISTING_ID,
            actor_id=SELLER_ID,
            actor_role=UserRole.SELLER,
        )
        raise AssertionError("expected ConversationServiceError")
    except ConversationServiceError as exc:
        assert "buyer_id" in str(exc)


def test_list_conversations_only_own() -> None:
    mine = _open_thread(BUYER_ID)
    conversation_service.create_conversation(
        listing_id=LISTING_ID,
        actor_id=OTHER_BUYER_ID,
        actor_role=UserRole.BUYER,
    )
    items, total = conversation_service.list_conversations(BUYER_ID)
    assert total == 1
    assert items[0].id == mine


def test_post_and_list_messages() -> None:
    conv_id = _open_thread()
    msg = conversation_service.post_message(
        conversation_id=conv_id,
        sender_id=BUYER_ID,
        body="Is this space free next week?",
    )
    assert msg.flagged is False
    items, total = conversation_service.list_messages(conv_id)
    assert total == 1
    assert items[0].body.startswith("Is this space")


def test_non_participant_cannot_post() -> None:
    conv_id = _open_thread()
    try:
        conversation_service.post_message(
            conversation_id=conv_id,
            sender_id=OTHER_BUYER_ID,
            body="sneak",
        )
        raise AssertionError("expected ConversationServiceError")
    except ConversationServiceError as exc:
        assert "participants" in str(exc).lower()


def test_off_platform_leakage_flags_but_does_not_block() -> None:
    conv_id = _open_thread()
    email = conversation_service.post_message(
        conversation_id=conv_id,
        sender_id=BUYER_ID,
        body="Email me at brand@example.com please",
    )
    phone = conversation_service.post_message(
        conversation_id=conv_id,
        sender_id=SELLER_ID,
        body="Call 07700 900123 instead",
    )
    phrase = conversation_service.post_message(
        conversation_id=conv_id,
        sender_id=BUYER_ID,
        body="Can you contact me outside the platform?",
    )
    assert email.flagged is True
    assert phone.flagged is True
    assert phrase.flagged is True
    items, total = conversation_service.list_messages(conv_id)
    assert total == 3


def test_seller_avg_response_time_stored() -> None:
    conv_id = _open_thread()
    inbound = conversation_service.post_message(
        conversation_id=conv_id,
        sender_id=BUYER_ID,
        body="Quick question",
    )
    store.update_message(
        inbound.id,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=120),
    )
    conversation_service.post_message(
        conversation_id=conv_id,
        sender_id=SELLER_ID,
        body="Yes, still available",
    )
    conv = store.get_conversation(conv_id)
    assert conv is not None
    assert conv.seller_response_sample_count == 1
    assert conv.seller_avg_response_seconds is not None
    # rewind was 120s; allow clock skew from create timestamps
    assert 118 <= conv.seller_avg_response_seconds <= 125
    profile = store.get_seller(SELLER_ID)
    assert profile is not None
    assert profile.response_sample_count == 1
    assert profile.avg_response_seconds is not None
    assert 118 <= profile.avg_response_seconds <= 125


def test_detect_off_platform_helpers() -> None:
    assert conversation_service.detect_off_platform_leakage("hello") is False
    assert conversation_service.detect_off_platform_leakage("ping me on WhatsApp") is True
    assert conversation_service.detect_off_platform_leakage("reach me at 07123456789") is True


def test_http_create_list_and_messages() -> None:
    buyer = _client_as(BUYER_ID, UserRole.BUYER)
    created = buyer.post("/api/conversations", json={"listing_id": LISTING_ID})
    assert created.status_code == 201
    conv_id = created.json()["id"]

    listed = buyer.get("/api/conversations")
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert listed.json()["items"][0]["id"] == conv_id

    sent = buyer.post(
        f"/api/conversations/{conv_id}/messages",
        json={"body": "Hello from the buyer"},
    )
    assert sent.status_code == 201
    assert sent.json()["flagged"] is False

    messages = buyer.get(f"/api/conversations/{conv_id}/messages")
    assert messages.status_code == 200
    assert messages.json()["total"] == 1


def test_http_non_participant_forbidden() -> None:
    conv_id = _open_thread()
    other = _client_as(OTHER_BUYER_ID, UserRole.BUYER)
    res = other.get(f"/api/conversations/{conv_id}/messages")
    assert res.status_code == 403
    posted = other.post(
        f"/api/conversations/{conv_id}/messages",
        json={"body": "nope"},
    )
    assert posted.status_code == 403


def test_http_create_idempotent_200() -> None:
    buyer = _client_as(BUYER_ID, UserRole.BUYER)
    first = buyer.post("/api/conversations", json={"listing_id": LISTING_ID})
    second = buyer.post("/api/conversations", json={"listing_id": LISTING_ID})
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_http_seller_list_includes_overall_avg() -> None:
    conv_id = _open_thread()
    inbound = conversation_service.post_message(
        conversation_id=conv_id,
        sender_id=BUYER_ID,
        body="Hi",
    )
    store.update_message(
        inbound.id,
        created_at=datetime.now(timezone.utc) - timedelta(seconds=30),
    )
    conversation_service.post_message(
        conversation_id=conv_id,
        sender_id=SELLER_ID,
        body="Hello",
    )
    seller = _client_as(SELLER_ID, UserRole.SELLER)
    res = seller.get("/api/conversations")
    assert res.status_code == 200
    body = res.json()
    assert body["total"] == 1
    assert body["seller_avg_response_seconds"] is not None
    assert body["items"][0]["seller_avg_response_seconds"] is not None
