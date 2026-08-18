import {
  apiFetch,
  apiFetchOptional,
  ApiError,
  isMissingEndpoint,
} from "@/components/buyer/api-client";
import {
  BOOKING_STATUS_LABELS,
  BookingStatus,
  isBookingStatus,
} from "@marketplays/shared";

export interface BuyerBooking {
  id: string;
  listing_id: string;
  listing_title?: string;
  status: string;
  start_date: string;
  end_date: string;
  total_pence: number;
  rating?: number | null;
  spaces?: number;
}

export interface BuyerAnalytics {
  spend30dPence: number;
  activeCampaigns: number;
  avgCostPerWeeklyReachPence: number;
  paymentsDuePence: number;
  bookings: BuyerBooking[];
}

function asBooking(raw: unknown): BuyerBooking | null {
  if (!raw || typeof raw !== "object") return null;
  const rec = raw as Record<string, unknown>;
  const id = rec.id ?? rec.booking_id ?? rec.bookingId;
  if (id == null) return null;
  return {
    id: String(id),
    listing_id: String(rec.listing_id ?? rec.listingId ?? ""),
    listing_title:
      rec.listing_title != null
        ? String(rec.listing_title)
        : rec.name != null
          ? String(rec.name)
          : rec.title != null
            ? String(rec.title)
            : undefined,
    status: String(rec.status ?? ""),
    start_date: String(rec.start_date ?? rec.startDate ?? rec.dateFrom ?? ""),
    end_date: String(rec.end_date ?? rec.endDate ?? rec.dateTo ?? ""),
    total_pence: Number(rec.total_pence ?? rec.totalPence ?? 0),
    rating:
      rec.rating == null ? null : Number(rec.rating),
    spaces: rec.spaces != null ? Number(rec.spaces) : 1,
  };
}

function extractBookings(payload: unknown): BuyerBooking[] {
  if (!payload) return [];
  if (Array.isArray(payload)) {
    return payload.map(asBooking).filter((b): b is BuyerBooking => b !== null);
  }
  if (typeof payload === "object") {
    const rec = payload as Record<string, unknown>;
    const nested =
      rec.items ?? rec.bookings ?? rec.campaigns ?? rec.results ?? rec.data;
    if (Array.isArray(nested)) {
      return nested.map(asBooking).filter((b): b is BuyerBooking => b !== null);
    }
  }
  return [];
}

function num(rec: Record<string, unknown>, ...keys: string[]): number {
  for (const key of keys) {
    const value = rec[key];
    if (typeof value === "number" && Number.isFinite(value)) return value;
    if (typeof value === "string" && value.trim() !== "" && !Number.isNaN(Number(value))) {
      return Number(value);
    }
  }
  return 0;
}

const ACTIVE = new Set<string>([
  BookingStatus.Confirmed,
  BookingStatus.Live,
  BookingStatus.Awaiting_Proof,
  BookingStatus.Awaiting_Buyer_Review,
]);

function kpisFromBookings(bookings: BuyerBooking[]): Omit<BuyerAnalytics, "bookings"> {
  const now = Date.now();
  const cutoff = now - 30 * 24 * 60 * 60 * 1000;
  const spend30dPence = bookings.reduce((sum, b) => {
    const t = Date.parse(b.start_date);
    if (!Number.isFinite(t) || t >= cutoff) return sum + (b.total_pence || 0);
    return sum;
  }, 0);
  return {
    spend30dPence,
    activeCampaigns: bookings.filter((b) => ACTIVE.has(b.status)).length,
    avgCostPerWeeklyReachPence: 0,
    paymentsDuePence: bookings
      .filter((b) => b.status === BookingStatus.Pending_Payment)
      .reduce((sum, b) => sum + (b.total_pence || 0), 0),
  };
}

/**
 * Prefer GET /api/bookings (list). If Agent 3 did not add it (404/405),
 * fall back to GET /api/analytics/buyer.
 */
export async function fetchBuyerCampaigns(): Promise<
  | { ok: true; data: BuyerAnalytics }
  | { ok: false; error: string; status?: number }
> {
  try {
    const listResult = await apiFetchOptional<unknown>("/api/bookings", {
      auth: true,
    });
    if (listResult.data != null) {
      const bookings = extractBookings(listResult.data);
      return {
        ok: true,
        data: { ...kpisFromBookings(bookings), bookings },
      };
    }

    const analytics = await apiFetch<unknown>("/api/analytics/buyer", {
      auth: true,
    });
    const rec =
      analytics && typeof analytics === "object"
        ? (analytics as Record<string, unknown>)
        : {};
    const bookings = extractBookings(analytics);
    const fromBookings = kpisFromBookings(bookings);
    return {
      ok: true,
      data: {
        spend30dPence:
          num(rec, "spend_30d_pence", "spend30dPence", "spend_pence") ||
          fromBookings.spend30dPence,
        activeCampaigns:
          num(rec, "active_campaigns", "activeCampaigns") ||
          fromBookings.activeCampaigns,
        avgCostPerWeeklyReachPence: num(
          rec,
          "avg_cost_per_weekly_reach_pence",
          "avgCostPerWeeklyReachPence",
          "avg_cis",
        ),
        paymentsDuePence:
          num(rec, "payments_due_pence", "paymentsDuePence") ||
          fromBookings.paymentsDuePence,
        bookings,
      },
    };
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 401) {
        return { ok: false, error: "Log in to view campaigns.", status: 401 };
      }
      if (isMissingEndpoint(err.status)) {
        return {
          ok: false,
          error:
            "Campaigns API is not available yet (GET /api/bookings and GET /api/analytics/buyer).",
          status: err.status,
        };
      }
      return { ok: false, error: err.message, status: err.status };
    }
    return { ok: false, error: "Could not load campaigns." };
  }
}

export async function fetchBuyerBooking(
  id: string,
): Promise<
  | { ok: true; booking: BuyerBooking }
  | { ok: false; error: string; status?: number }
> {
  try {
    const raw = await apiFetch<unknown>(`/api/bookings/${id}`, { auth: true });
    const booking = asBooking(raw);
    if (!booking) {
      return { ok: false, error: "Unexpected booking response." };
    }
    return { ok: true, booking };
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 404) {
        return {
          ok: false,
          error: "Booking not found.",
          status: 404,
        };
      }
      if (err.status === 401) {
        return { ok: false, error: "Log in to view this booking.", status: 401 };
      }
      return { ok: false, error: err.message, status: err.status };
    }
    return { ok: false, error: "Could not load booking." };
  }
}

export function bookingStatusLabel(status: string): string {
  if (isBookingStatus(status)) {
    return BOOKING_STATUS_LABELS[status];
  }
  return status;
}
