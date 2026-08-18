/**
 * Conversations API client for the messages page.
 */

import { api, ApiError, isMissingEndpoint } from "@/lib/api";

const MP_USER_ID_KEY = "mp_user_id";

export class MessagesApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function toMessagesError(err: unknown): MessagesApiError {
  if (err instanceof MessagesApiError) return err;
  if (err instanceof ApiError) return new MessagesApiError(err.message, err.status);
  return new MessagesApiError("Request failed", 0);
}

async function messagesFetch<T>(path: string, init?: RequestInit): Promise<T> {
  try {
    return await api<T>(path, init);
  } catch (err) {
    throw toMessagesError(err);
  }
}

async function messagesGetOptional<T>(
  path: string,
): Promise<T | null> {
  try {
    return await api<T>(path, { method: "GET" });
  } catch (err) {
    const mapped = toMessagesError(err);
    if (isMissingEndpoint(mapped.status) || mapped.status === 0) return null;
    throw mapped;
  }
}

function unwrapItems<T>(data: unknown, keys: string[]): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const rec = data as Record<string, unknown>;
    for (const key of keys) {
      if (Array.isArray(rec[key])) return rec[key] as T[];
    }
  }
  return [];
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

export interface ConversationThreadDto {
  id: string;
  counterpartName: string;
  listingTitle: string;
  lastPreview: string;
  updatedAt: string;
  unread: boolean;
}

export interface ConversationMessageDto {
  id: string;
  fromSelf: boolean;
  body: string;
  sentAt: string;
}

function currentUserId(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(MP_USER_ID_KEY) ?? "";
}

export function mapConversation(raw: unknown): ConversationThreadDto {
  const rec = asRecord(raw);
  const listing = asRecord(rec.listing);
  const counterpart = asRecord(rec.counterpart ?? rec.other_user ?? rec.seller ?? rec.buyer);
  const last = asRecord(rec.last_message ?? rec.lastMessage);
  return {
    id: str(rec.id),
    counterpartName: str(
      rec.counterpart_name ??
        rec.counterpartName ??
        counterpart.full_name ??
        counterpart.name,
      "Conversation",
    ),
    listingTitle: str(
      rec.listing_title ?? rec.listingTitle ?? listing.title,
      "",
    ),
    lastPreview: str(
      rec.last_preview ??
        rec.lastPreview ??
        last.body ??
        rec.preview,
    ),
    updatedAt: str(
      rec.updated_at ?? rec.updatedAt ?? last.created_at ?? rec.created_at,
    ),
    unread: Boolean(rec.unread ?? rec.has_unread ?? rec.unread_count),
  };
}

export function mapMessage(raw: unknown): ConversationMessageDto {
  const rec = asRecord(raw);
  const uid = currentUserId();
  const senderId = str(rec.sender_id ?? rec.senderId ?? rec.user_id);
  const fromSelf =
    typeof rec.from_self === "boolean"
      ? rec.from_self
      : typeof rec.fromSelf === "boolean"
        ? rec.fromSelf
        : Boolean(uid && senderId && senderId === uid);
  return {
    id: str(rec.id),
    fromSelf,
    body: str(rec.body ?? rec.message ?? rec.content),
    sentAt: str(rec.sent_at ?? rec.sentAt ?? rec.created_at ?? rec.createdAt),
  };
}

export async function listConversations(): Promise<ConversationThreadDto[]> {
  const data = await messagesGetOptional<unknown>("/api/conversations");
  if (!data) return [];
  return unwrapItems<unknown>(data, ["items", "conversations"]).map(
    mapConversation,
  );
}

export async function listMessages(
  conversationId: string,
): Promise<ConversationMessageDto[]> {
  const data = await messagesGetOptional<unknown>(
    `/api/conversations/${conversationId}/messages`,
  );
  if (!data) return [];
  return unwrapItems<unknown>(data, ["items", "messages"]).map(mapMessage);
}

export async function sendMessage(
  conversationId: string,
  body: string,
): Promise<ConversationMessageDto> {
  const data = await messagesFetch<unknown>(
    `/api/conversations/${conversationId}/messages`,
    { method: "POST", body: JSON.stringify({ body }) },
  );
  return mapMessage(data);
}
