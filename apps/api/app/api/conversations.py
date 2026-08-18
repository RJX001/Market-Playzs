"""Messaging API — buyer↔seller threads. Participants only."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from app.api.deps import CurrentUser, require_role
from app.domain_enums import UserRole
from app.repositories.memory_store import ConversationRecord, store
from app.schemas.conversations import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    MessageCreate,
    MessageListResponse,
    MessageResponse,
)
from app.services import conversation_service
from app.services.conversation_service import ConversationServiceError

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def conversation_participant(
    conversation_id: str,
    user: CurrentUser = Depends(require_role(UserRole.BUYER, UserRole.SELLER)),
) -> ConversationRecord:
    """Resolve a thread and require the caller to be buyer or seller on it."""
    conversation = store.get_conversation(conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if user.id not in (conversation.buyer_id, conversation.seller_id):
        raise HTTPException(status_code=403, detail="Forbidden")
    return conversation


def _to_conversation_response(record: ConversationRecord) -> ConversationResponse:
    listing = store.get_listing(record.listing_id)
    return ConversationResponse(
        id=record.id,
        listing_id=record.listing_id,
        listing_title=listing.title if listing else None,
        buyer_id=record.buyer_id,
        seller_id=record.seller_id,
        last_message_preview=record.last_message_preview,
        last_message_at=record.last_message_at,
        seller_avg_response_seconds=record.seller_avg_response_seconds,
        created_at=record.created_at,
        updated_at=record.updated_at,
    )


def _to_message_response(record) -> MessageResponse:
    return MessageResponse(
        id=record.id,
        conversation_id=record.conversation_id,
        sender_id=record.sender_id,
        body=record.body,
        flagged=record.flagged,
        created_at=record.created_at,
    )


@router.post(
    "",
    response_model=ConversationResponse,
    summary="Create a conversation",
    description=(
        "Open a buyer↔seller thread tied to a listing, or return the existing "
        "thread for that listing and buyer. Buyers are the buyer on the thread; "
        "sellers must own the listing and pass buyer_id. HTTP 201 when created, "
        "200 when an existing thread is returned."
    ),
)
async def create_conversation(
    body: ConversationCreate,
    response: Response,
    user: CurrentUser = Depends(require_role(UserRole.BUYER, UserRole.SELLER)),
) -> ConversationResponse:
    try:
        conversation, created = conversation_service.create_conversation(
            listing_id=body.listing_id,
            actor_id=user.id,
            actor_role=user.role,
            buyer_id=body.buyer_id,
        )
    except ConversationServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    response.status_code = (
        status.HTTP_201_CREATED if created else status.HTTP_200_OK
    )
    return _to_conversation_response(conversation)


@router.get(
    "",
    response_model=ConversationListResponse,
    summary="List conversations",
    description=(
        "Paginated thread list for the authenticated user. Only threads where "
        "the caller is the buyer or seller are returned. Each item includes "
        "the per-thread seller average response time; when the caller is a "
        "seller, seller_avg_response_seconds on the payload is their overall "
        "average across threads."
    ),
)
async def list_conversations(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=20),
    user: CurrentUser = Depends(require_role(UserRole.BUYER, UserRole.SELLER)),
) -> ConversationListResponse:
    items, total = conversation_service.list_conversations(
        user.id, page=page, page_size=page_size
    )
    overall: float | None = None
    if user.role == UserRole.SELLER:
        overall = conversation_service.seller_avg_response_seconds(user.id)
    return ConversationListResponse(
        items=[_to_conversation_response(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        seller_avg_response_seconds=overall,
    )


@router.get(
    "/{conversation_id}/messages",
    response_model=MessageListResponse,
    summary="List conversation messages",
    description=(
        "Paginated messages in chronological order. Restricted to the buyer "
        "and seller on the thread. Flagged messages (off-platform leakage) "
        "are included — they are not hidden from participants."
    ),
)
async def list_messages(
    conversation: ConversationRecord = Depends(conversation_participant),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> MessageListResponse:
    items, total = conversation_service.list_messages(
        conversation.id, page=page, page_size=page_size
    )
    return MessageListResponse(
        items=[_to_message_response(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message",
    description=(
        "Post a message as a thread participant. Phone numbers, emails, and "
        "off-platform contact phrasing set flagged=true for admin moderation "
        "but the message is still delivered. Seller replies update the stored "
        "average response-time metric."
    ),
)
async def post_message(
    body: MessageCreate,
    conversation: ConversationRecord = Depends(conversation_participant),
    user: CurrentUser = Depends(require_role(UserRole.BUYER, UserRole.SELLER)),
) -> MessageResponse:
    try:
        message = conversation_service.post_message(
            conversation_id=conversation.id,
            sender_id=user.id,
            body=body.body,
        )
    except ConversationServiceError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return _to_message_response(message)
