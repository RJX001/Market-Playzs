"""Buyer↔seller messaging — threads tied to a listing.

Seller average response time is stored on the conversation and seller profile
(raw metric for later CIS breakdown; weighting is a separate decision).

Off-platform leakage is flagged, never blocked.
"""

from __future__ import annotations

import re

from app.domain_enums import ListingStatus, UserRole
from app.repositories.memory_store import (
    ConversationRecord,
    MessageRecord,
    new_id,
    store,
)

_PREVIEW_LEN = 160

# Phone / email / "take this off-platform" phrasing — flag for moderation.
_EMAIL_RE = re.compile(r"[A-Z0-9._%+\-]+@[A-Z0-9.\-]+\.[A-Z]{2,}", re.I)
_UK_MOBILE_RE = re.compile(
    r"(?<!\d)(?:\+44[\s\-]?|0)7(?:[\s\-]?\d){9}(?!\d)",
)
_DIGIT_RUN_RE = re.compile(r"(?:\+?\d[\s\-().]*){10,15}")
_PHRASE_RE = re.compile(
    r"contact me outside|contact outside|off[\s\-]?platform|"
    r"whats\s?app|text me|call me|email me|"
    r"reach me (?:on|at|outside)|message me on|dm me",
    re.I,
)


class ConversationServiceError(ValueError):
    """Domain validation error for conversation operations."""


def detect_off_platform_leakage(body: str) -> bool:
    """True when the message looks like phone, email, or off-platform contact."""
    if _EMAIL_RE.search(body):
        return True
    if _UK_MOBILE_RE.search(body):
        return True
    if _DIGIT_RUN_RE.search(body):
        return True
    if _PHRASE_RE.search(body):
        return True
    return False


def _preview(body: str) -> str:
    text = " ".join(body.split())
    if len(text) <= _PREVIEW_LEN:
        return text
    return text[: _PREVIEW_LEN - 1] + "…"


def _first_unanswered_buyer(
    messages: list[MessageRecord],
    *,
    buyer_id: str,
    seller_id: str,
) -> MessageRecord | None:
    first: MessageRecord | None = None
    for msg in messages:
        if msg.sender_id == buyer_id:
            if first is None:
                first = msg
        elif msg.sender_id == seller_id:
            first = None
    return first


def create_conversation(
    *,
    listing_id: str,
    actor_id: str,
    actor_role: UserRole,
    buyer_id: str | None = None,
) -> tuple[ConversationRecord, bool]:
    """
    Open (or return) a buyer↔seller thread for a listing.

    Returns (conversation, created).
    """
    listing = store.get_listing(listing_id)
    if not listing:
        raise ConversationServiceError("Listing not found")
    if listing.status != ListingStatus.PUBLISHED:
        raise ConversationServiceError("Listing is not published")

    if actor_role == UserRole.BUYER:
        resolved_buyer_id = actor_id
        if actor_id == listing.seller_id:
            raise ConversationServiceError("Cannot message your own listing")
    elif actor_role == UserRole.SELLER:
        if actor_id != listing.seller_id:
            raise ConversationServiceError("Only the listing seller may open this thread")
        if not buyer_id:
            raise ConversationServiceError("buyer_id is required when a seller creates a conversation")
        resolved_buyer_id = buyer_id
    else:
        raise ConversationServiceError("Only buyers and sellers may create conversations")

    existing = store.get_conversation_by_listing_buyer(listing_id, resolved_buyer_id)
    if existing:
        return existing, False

    record = ConversationRecord(
        id=new_id(),
        listing_id=listing_id,
        buyer_id=resolved_buyer_id,
        seller_id=listing.seller_id,
    )
    return store.create_conversation(record), True


def list_conversations(
    user_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
) -> tuple[list[ConversationRecord], int]:
    all_rows = store.list_conversations_for_user(user_id)
    total = len(all_rows)
    start = (page - 1) * page_size
    return all_rows[start : start + page_size], total


def seller_avg_response_seconds(seller_id: str) -> float | None:
    profile = store.get_seller(seller_id)
    if not profile:
        return None
    return profile.avg_response_seconds


def list_messages(
    conversation_id: str,
    *,
    page: int = 1,
    page_size: int = 50,
) -> tuple[list[MessageRecord], int]:
    all_rows = store.list_messages(conversation_id)
    total = len(all_rows)
    start = (page - 1) * page_size
    return all_rows[start : start + page_size], total


def post_message(
    *,
    conversation_id: str,
    sender_id: str,
    body: str,
) -> MessageRecord:
    conversation = store.get_conversation(conversation_id)
    if not conversation:
        raise ConversationServiceError("Conversation not found")
    if sender_id not in (conversation.buyer_id, conversation.seller_id):
        raise ConversationServiceError("Only participants may send messages")

    text = body.strip()
    if not text:
        raise ConversationServiceError("Message body cannot be empty")

    flagged = detect_off_platform_leakage(text)
    existing = store.list_messages(conversation_id)
    unanswered = _first_unanswered_buyer(
        existing,
        buyer_id=conversation.buyer_id,
        seller_id=conversation.seller_id,
    )

    record = MessageRecord(
        id=new_id(),
        conversation_id=conversation_id,
        sender_id=sender_id,
        body=text,
        flagged=flagged,
    )
    created = store.create_message(record)

    if sender_id == conversation.seller_id and unanswered is not None:
        delta = (created.created_at - unanswered.created_at).total_seconds()
        if delta >= 0:
            store.record_seller_response(
                conversation_id=conversation_id,
                seller_id=conversation.seller_id,
                sample_seconds=delta,
            )

    store.update_conversation(
        conversation_id,
        last_message_preview=_preview(text),
        last_message_at=created.created_at,
    )
    return created
