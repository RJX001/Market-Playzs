import { api, ApiError, isMissingEndpoint } from "@/lib/api";
import {
  BookingStatus,
  type BookingStatus as BookingStatusType,
  type Category,
} from "@marketplays/shared";
import type { CisFactor } from "@/components/seller/CisBreakdownCard";
import type {
  MonthlyRevenuePoint,
  SellerBookingActivity,
  SellerListingStub,
} from "@/components/seller/stub-data";

export const MP_TOKEN_KEY = "mp_access_token";
export const MP_ROLE_KEY = "mp_role";
export const MP_USER_ID_KEY = "mp_user_id";

const BOOKING_STATUSES = new Set<string>(Object.values(BookingStatus));

export class SellerApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

function toSellerError(err: unknown): SellerApiError {
  if (err instanceof SellerApiError) return err;
  if (err instanceof ApiError) return new SellerApiError(err.message, err.status);
  return new SellerApiError("Request failed", 0);
}

export async function sellerFetch<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  try {
    return await api<T>(path, init);
  } catch (err) {
    throw toSellerError(err);
  }
}

/** GET that treats missing endpoints as empty rather than throwing. */
export async function sellerGetOptional<T>(
  path: string,
): Promise<{ data: T | null; status: number }> {
  try {
    const data = await api<T>(path, { method: "GET" });
    return { data, status: 200 };
  } catch (err) {
    const mapped = toSellerError(err);
    if (isMissingEndpoint(mapped.status) || mapped.status === 0) {
      return { data: null, status: mapped.status };
    }
    throw mapped;
  }
}

export function unwrapItems<T>(data: unknown, keys: string[] = ["items"]): T[] {
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === "object") {
    const rec = data as Record<string, unknown>;
    for (const key of keys) {
      if (Array.isArray(rec[key])) return rec[key] as T[];
    }
  }
  return [];
}

function num(value: unknown, fallback = 0): number {
  const n = Number(value);
  return Number.isFinite(n) ? n : fallback;
}

function str(value: unknown, fallback = ""): string {
  return typeof value === "string" ? value : fallback;
}

function asRecord(value: unknown): Record<string, unknown> {
  return value && typeof value === "object"
    ? (value as Record<string, unknown>)
    : {};
}

export interface ListingPayload {
  title: string;
  description: string;
  category: Category;
  price_per_day_pence: number;
  lat: number;
  lng: number;
  images: string[];
  audience_tags?: string[];
  booking_types?: string[];
}

export interface ListingApiRecord {
  id: string;
  title: string;
  description?: string;
  category: Category;
  status: string;
  price_per_day_pence: number;
  lat?: number;
  lng?: number;
  images?: string[];
  cis_score: number | null;
  booking_types?: string[];
}

export async function createListing(
  body: ListingPayload,
): Promise<ListingApiRecord> {
  return sellerFetch<ListingApiRecord>("/api/listings", {
    method: "POST",
    body: JSON.stringify(body),
  });
}

export async function patchListing(
  listingId: string,
  body: Partial<ListingPayload>,
): Promise<ListingApiRecord> {
  return sellerFetch<ListingApiRecord>(`/api/listings/${listingId}`, {
    method: "PATCH",
    body: JSON.stringify(body),
  });
}

export async function publishListing(
  listingId: string,
): Promise<{ id: string; status: string; message: string }> {
  return sellerFetch(`/api/listings/${listingId}/publish`, { method: "POST" });
}

export async function getListing(
  listingId: string,
): Promise<ListingApiRecord | null> {
  const { data } = await sellerGetOptional<ListingApiRecord>(
    `/api/listings/${listingId}`,
  );
  return data;
}

export async function listSellerListings(): Promise<ListingApiRecord[]> {
  const mine = await sellerGetOptional<unknown>("/api/listings/mine");
  if (mine.data) {
    return unwrapItems<ListingApiRecord>(mine.data, ["items", "listings"]);
  }
  return [];
}

export async function uploadMedia(
  file: File,
  purpose: "listing_image" | "proof" = "listing_image",
): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const data = await sellerFetch<Record<string, unknown>>(
    `/api/media/upload?purpose=${encodeURIComponent(purpose)}`,
    {
      method: "POST",
      body: form,
    },
  );
  const url = str(data.url || data.file_url || data.media_url || data.path);
  if (!url) throw new SellerApiError("Upload did not return a file URL", 500);
  return url;
}

export async function createConnectAccountLink(urls: {
  refresh_url: string;
  return_url: string;
}): Promise<{ url: string; stripe_account_id: string }> {
  return sellerFetch("/api/payments/connect/account-link", {
    method: "POST",
    body: JSON.stringify(urls),
  });
}

export interface SellerAnalytics {
  revenue30dPence: number;
  revenueDelta?: string;
  activeBookings: number;
  avgCisScore: number;
  occupancyRatePct: number;
  occupancy30d: number[];
  cisBreakdown: CisFactor[];
  revenue12m: MonthlyRevenuePoint[];
  pendingPayoutPence: number;
  recentBookings: SellerBookingActivity[];
}

export function mapSellerAnalytics(raw: unknown): SellerAnalytics {
  const rec = asRecord(raw);
  const breakdownRaw = rec.cis_breakdown ?? rec.cisBreakdown ?? rec.cis_trend;
  const cisBreakdown: CisFactor[] = unwrapItems<{
    label?: string;
    name?: string;
    value?: number;
    score?: number;
  }>(breakdownRaw, ["items", "factors"]).map((f) => ({
    label: str(f.label ?? f.name, "Factor"),
    value: num(f.value ?? f.score),
  }));
  const seriesRaw = rec.revenue_12m ?? rec.revenue12m ?? rec.revenue_series;
  const revenue12m: MonthlyRevenuePoint[] = unwrapItems<{
    month?: string;
    label?: string;
    revenue_pence?: number;
    revenuePence?: number;
  }>(seriesRaw, ["items"]).map((p) => ({
    month: str(p.month ?? p.label, ""),
    revenuePence: num(p.revenue_pence ?? p.revenuePence),
  }));
  const occ = rec.occupancy_30d ?? rec.occupancy30d ?? rec.occupancy;
  const occupancy30d = Array.isArray(occ) ? occ.map((n) => num(n)) : [];
  const bookingsRaw =
    rec.recent_bookings ?? rec.recentBookings ?? rec.booking_activity;
  return {
    revenue30dPence: num(
      rec.revenue_30d_pence ?? rec.revenue30dPence ?? rec.revenue_pence,
    ),
    revenueDelta:
      str(rec.revenue_delta ?? rec.revenueDelta, "") || undefined,
    activeBookings: num(rec.active_bookings ?? rec.activeBookings),
    avgCisScore: num(rec.avg_cis_score ?? rec.avgCisScore ?? rec.cis_score),
    occupancyRatePct: num(
      rec.occupancy_rate_pct ?? rec.occupancyRatePct ?? rec.occupancy_rate,
    ),
    occupancy30d,
    cisBreakdown,
    revenue12m,
    pendingPayoutPence: num(
      rec.pending_payout_pence ?? rec.pendingPayoutPence,
    ),
    recentBookings: unwrapItems<unknown>(bookingsRaw, [
      "items",
      "bookings",
    ]).map(mapSellerBooking),
  };
}

export async function getSellerAnalytics(): Promise<SellerAnalytics | null> {
  const { data } = await sellerGetOptional<unknown>("/api/analytics/seller");
  return data ? mapSellerAnalytics(data) : null;
}

export async function getSellerPayouts(): Promise<{ pendingPence: number }> {
  const { data } = await sellerGetOptional<unknown>("/api/payments/payouts");
  if (!data) return { pendingPence: 0 };
  const rec = asRecord(data);
  const items = unwrapItems<{
    amount_pence?: number;
    amountPence?: number;
    status?: string;
  }>(data, ["items", "payouts"]);
  const pendingFromItems = items
    .filter((p) => {
      const s = str(p.status).toLowerCase();
      return !s || s === "pending" || s === "in_transit";
    })
    .reduce((sum, p) => sum + num(p.amount_pence ?? p.amountPence), 0);
  return {
    pendingPence: num(
      rec.pending_pence ?? rec.pending_payout_pence ?? rec.pendingPayoutPence,
      pendingFromItems,
    ),
  };
}

function formatOccurredAt(value: unknown): string {
  const raw = str(value);
  if (!raw) return "";
  const d = new Date(raw);
  if (Number.isNaN(d.getTime())) return raw;
  return d.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function coerceBookingStatus(value: unknown): BookingStatusType {
  const s = str(value);
  if (BOOKING_STATUSES.has(s)) return s as BookingStatusType;
  return BookingStatus.Pending_Payment;
}

export function mapSellerBooking(raw: unknown): SellerBookingActivity {
  const rec = asRecord(raw);
  const listing = asRecord(rec.listing);
  const buyer = asRecord(rec.buyer);
  return {
    id: str(rec.id ?? rec.booking_id),
    listingTitle: str(
      rec.listing_title ?? rec.listingTitle ?? listing.title ?? rec.listing_id,
      "Listing",
    ),
    buyerName: str(
      rec.buyer_name ?? rec.buyerName ?? buyer.full_name ?? rec.buyer_id,
      "Buyer",
    ),
    status: coerceBookingStatus(rec.status),
    amountPence: num(
      rec.amount_pence ?? rec.amountPence ?? rec.total_pence ?? rec.totalPence,
    ),
    countdown: str(rec.countdown) || undefined,
    subLabel: str(rec.sub_label ?? rec.subLabel) || undefined,
    occurredAt: formatOccurredAt(
      rec.occurred_at ?? rec.occurredAt ?? rec.created_at ?? rec.updated_at,
    ),
    proofUrl: str(rec.proof_url ?? rec.proofUrl) || null,
  };
}

export async function listSellerBookings(): Promise<SellerBookingActivity[]> {
  const { data } = await sellerGetOptional<unknown>("/api/bookings");
  if (!data) return [];
  return unwrapItems<unknown>(data, ["items", "bookings"]).map(mapSellerBooking);
}

export async function declineBooking(bookingId: string): Promise<void> {
  await sellerFetch(`/api/bookings/${bookingId}/cancel`, { method: "POST" });
}

export async function uploadBookingProof(
  bookingId: string,
  mediaUrl?: string,
): Promise<void> {
  await sellerFetch(`/api/bookings/${bookingId}/proof`, {
    method: "POST",
    body: JSON.stringify(mediaUrl ? { url: mediaUrl } : {}),
  });
}

export function mapSellerListing(raw: ListingApiRecord): SellerListingStub {
  const status = str(raw.status).toLowerCase();
  const listingStatus: SellerListingStub["status"] =
    status === "published"
      ? "published"
      : status === "paused" || status === "suspended"
        ? "paused"
        : "draft";
  return {
    id: raw.id,
    title: raw.title,
    category: raw.category,
    cisScore: raw.cis_score,
    status: listingStatus,
    pricePerDayPence: raw.price_per_day_pence,
    imageCount: Array.isArray(raw.images) ? raw.images.length : 0,
  };
}
