/**
 * Admin API client — thin wrapper around `@/lib/api`.
 */

import { api, ApiError, isMissingEndpoint } from "@/lib/api";

export type DisputeResolutionAction =
  | "approve_seller"
  | "full_refund"
  | "partial_refund";

export interface ResolveDisputePayload {
  bookingId: string;
  action: DisputeResolutionAction;
  /** Required when action is partial_refund — integer percent 1–99 */
  refundPercent?: number;
  reason: string;
}

export interface SuspendUserPayload {
  userId: string;
  reason: string;
}

export interface CisOverridePayload {
  listingId: string;
  cisScore: number;
  reason?: string;
}

export interface SuspendListingPayload {
  listingId: string;
  reason: string;
}

export class AdminApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function toAdminError(err: unknown): AdminApiError {
  if (err instanceof AdminApiError) return err;
  if (err instanceof ApiError) return new AdminApiError(err.message, err.status);
  return new AdminApiError("Request failed", 0);
}

export async function adminFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  try {
    return await api<T>(path, init);
  } catch (err) {
    throw toAdminError(err);
  }
}

export async function adminGetOptional<T>(
  path: string,
): Promise<T | null> {
  try {
    return await api<T>(path, { method: "GET" });
  } catch (err) {
    const mapped = toAdminError(err);
    if (isMissingEndpoint(mapped.status) || mapped.status === 0) return null;
    throw mapped;
  }
}

export function unwrapItems<T>(data: unknown, keys: string[]): T[] {
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

function num(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

/** POST /api/admin/bookings/{id}/resolve-dispute */
export async function resolveDispute(
  payload: ResolveDisputePayload,
): Promise<{ ok: boolean; path: string; message?: string }> {
  const path = `/api/admin/bookings/${payload.bookingId}/resolve-dispute`;
  const data = await adminFetch<{ message?: string }>(path, {
    method: "POST",
    body: JSON.stringify({
      resolution: payload.action,
      partial_percent:
        payload.action === "partial_refund" ? payload.refundPercent : undefined,
      reason: payload.reason,
    }),
  });
  return { ok: true, path, message: data?.message };
}

/** POST /api/admin/users/{id}/suspend */
export async function suspendUser(
  payload: SuspendUserPayload,
): Promise<{ ok: boolean; path: string }> {
  const path = `/api/admin/users/${payload.userId}/suspend`;
  await adminFetch(path, {
    method: "POST",
    body: JSON.stringify({ reason: payload.reason }),
  });
  return { ok: true, path };
}

/** POST /api/admin/listings/{id}/cis-override */
export async function overrideCis(
  payload: CisOverridePayload,
): Promise<{ ok: boolean; path: string }> {
  const path = `/api/admin/listings/${payload.listingId}/cis-override`;
  await adminFetch(path, {
    method: "POST",
    body: JSON.stringify({
      cis_score: payload.cisScore,
      reason: payload.reason ?? "Admin CIS override",
    }),
  });
  return { ok: true, path };
}

/** POST /api/admin/listings/{id}/suspend */
export async function suspendListing(
  payload: SuspendListingPayload,
): Promise<{ ok: boolean; path: string }> {
  const path = `/api/admin/listings/${payload.listingId}/suspend`;
  await adminFetch(path, {
    method: "POST",
    body: JSON.stringify({ reason: payload.reason }),
  });
  return { ok: true, path };
}

export async function approveListing(
  listingId: string,
): Promise<{ ok: boolean }> {
  await adminFetch(`/api/admin/listings/${listingId}/approve`, {
    method: "POST",
  });
  return { ok: true };
}

export async function rejectListing(
  listingId: string,
  reason = "Rejected by admin",
): Promise<{ ok: boolean }> {
  await adminFetch(`/api/admin/listings/${listingId}/reject`, {
    method: "POST",
    body: JSON.stringify({ reason }),
  });
  return { ok: true };
}

export interface AdminReport {
  gmvPence: number;
  activeListings: number;
  pendingModeration: number;
  disputesOpen: number;
  listingsSuspended: number;
}

export function mapAdminReport(raw: unknown): AdminReport {
  const rec = asRecord(raw);
  return {
    gmvPence: num(rec.gmv_pence ?? rec.gmvPence ?? rec.gmv),
    activeListings: num(
      rec.active_listings ?? rec.activeListings ?? rec.listings,
    ),
    pendingModeration: num(
      rec.pending_moderation ?? rec.pendingModeration ?? rec.moderation_queue,
    ),
    disputesOpen: num(
      rec.disputes_open ?? rec.disputesOpen ?? rec.open_disputes,
    ),
    listingsSuspended: num(
      rec.listings_suspended ?? rec.listingsSuspended ?? rec.suspended_listings,
    ),
  };
}

export async function getAdminReport(): Promise<AdminReport | null> {
  const data = await adminGetOptional<unknown>("/api/admin/report");
  return data ? mapAdminReport(data) : null;
}

export function mapModerationItem(raw: unknown): {
  id: string;
  title: string;
  sellerName: string;
  category: string;
  submittedAt: string;
} {
  const rec = asRecord(raw);
  const seller = asRecord(rec.seller);
  return {
    id: str(rec.id ?? rec.listing_id),
    title: str(rec.title, "Listing"),
    sellerName: str(
      rec.seller_name ?? rec.sellerName ?? seller.full_name ?? seller.name,
      "Seller",
    ),
    category: str(rec.category),
    submittedAt: str(
      rec.submitted_at ?? rec.submittedAt ?? rec.created_at ?? rec.updated_at,
    ),
  };
}

export async function getModerationQueue() {
  const data = await adminGetOptional<unknown>("/api/admin/moderation/listings");
  if (!data) return null;
  return unwrapItems<unknown>(data, ["items", "listings", "queue"]).map(
    mapModerationItem,
  );
}

export function mapAdminDispute(raw: unknown): {
  id: string;
  bookingId: string;
  listingTitle: string;
  buyerName: string;
  sellerName: string;
  amountPence: number;
  reason: string;
  openedAt: string;
  status: "open" | "resolved";
  firstDecisionDueAt?: string;
} {
  const rec = asRecord(raw);
  const listing = asRecord(rec.listing);
  const buyer = asRecord(rec.buyer);
  const seller = asRecord(rec.seller);
  const statusRaw = str(rec.status).toLowerCase();
  return {
    id: str(rec.id ?? rec.dispute_id),
    bookingId: str(rec.booking_id ?? rec.bookingId ?? rec.id),
    listingTitle: str(
      rec.listing_title ?? rec.listingTitle ?? listing.title,
      "Listing",
    ),
    buyerName: str(
      rec.buyer_name ?? rec.buyerName ?? buyer.full_name ?? buyer.name,
      "Buyer",
    ),
    sellerName: str(
      rec.seller_name ?? rec.sellerName ?? seller.full_name ?? seller.name,
      "Seller",
    ),
    amountPence: num(
      rec.amount_pence ?? rec.amountPence ?? rec.total_pence,
    ),
    reason: str(rec.reason ?? rec.issue, ""),
    openedAt: str(rec.opened_at ?? rec.openedAt ?? rec.created_at),
    status:
      statusRaw === "resolved" || statusRaw === "closed" ? "resolved" : "open",
    firstDecisionDueAt: str(
      rec.first_decision_due_at ?? rec.firstDecisionDueAt,
    ) || undefined,
  };
}

export async function getAdminDisputes() {
  const data = await adminGetOptional<unknown>("/api/admin/disputes");
  if (!data) return null;
  return unwrapItems<unknown>(data, ["items", "disputes"]).map(mapAdminDispute);
}

export function mapAdminUser(raw: unknown): {
  id: string;
  email: string;
  name: string;
  role: "buyer" | "seller" | "admin";
  status: "active" | "suspended";
  createdAt: string;
} {
  const rec = asRecord(raw);
  const roleRaw = str(rec.role).toLowerCase();
  const role: "buyer" | "seller" | "admin" =
    roleRaw === "seller" || roleRaw === "admin" ? roleRaw : "buyer";
  const suspended = Boolean(rec.is_suspended ?? rec.suspended);
  return {
    id: str(rec.id),
    email: str(rec.email),
    name: str(rec.name ?? rec.full_name ?? rec.fullName, rec.email as string),
    role,
    status: suspended || str(rec.status) === "suspended" ? "suspended" : "active",
    createdAt: str(rec.created_at ?? rec.createdAt).slice(0, 10),
  };
}

export async function getAdminUsers() {
  const data = await adminGetOptional<unknown>("/api/admin/users");
  if (!data) return null;
  return unwrapItems<unknown>(data, ["items", "users"]).map(mapAdminUser);
}

export function mapAdminListing(raw: unknown): {
  id: string;
  title: string;
  sellerName: string;
  category: string;
  cisScore: number | null;
  isCisOverridden: boolean;
  status: "live" | "draft" | "suspended";
  suspensionReason: string | null;
} {
  const rec = asRecord(raw);
  const seller = asRecord(rec.seller);
  const statusRaw = str(rec.status).toLowerCase();
  const status: "live" | "draft" | "suspended" =
    statusRaw === "suspended"
      ? "suspended"
      : statusRaw === "draft"
        ? "draft"
        : "live";
  const cis = rec.cis_score ?? rec.cisScore;
  return {
    id: str(rec.id),
    title: str(rec.title, "Listing"),
    sellerName: str(
      rec.seller_name ?? rec.sellerName ?? seller.full_name ?? seller.name,
      "Seller",
    ),
    category: str(rec.category),
    cisScore: cis === null || cis === undefined ? null : num(cis),
    isCisOverridden: Boolean(rec.is_cis_overridden ?? rec.isCisOverridden),
    status,
    suspensionReason: str(rec.suspension_reason ?? rec.suspensionReason) || null,
  };
}

export async function getAdminListings() {
  const data = await adminGetOptional<unknown>("/api/admin/listings");
  if (!data) return null;
  return unwrapItems<unknown>(data, ["items", "listings"]).map(mapAdminListing);
}
