"""Conversation and message request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ConversationCreate(BaseModel):
    listing_id: str
    # Required when a seller opens a thread; ignored (set from auth) for buyers.
    buyer_id: str | None = None


class ConversationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    listing_id: str
    listing_title: str | None = None
    buyer_id: str
    seller_id: str
    last_message_preview: str | None
    last_message_at: datetime | None
    seller_avg_response_seconds: float | None
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationResponse]
    total: int
    page: int
    page_size: int
    # Seller-wide average when the current user is a seller; otherwise null.
    seller_avg_response_seconds: float | None = None


class MessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    sender_id: str
    body: str
    flagged: bool
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    total: int
    page: int
    page_size: int
