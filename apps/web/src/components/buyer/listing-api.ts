import {
  apiFetch,
  apiFetchOptional,
  ApiError,
} from "@/components/buyer/api-client";
import {
  isoDate,
  mapApiListing,
  type ApiListing,
  type AvailabilityDayDto,
} from "@/components/buyer/listing-mapper";
import { getMockListingById } from "@/components/buyer/mock-listings";
import type { BuyerListing } from "@/components/buyer/types";

export interface ListingReview {
  id?: string;
  rating: number;
  comment?: string | null;
  created_at?: string;
}

export async function fetchListingById(id: string): Promise<{
  listing: BuyerListing | null;
  source: "api" | "mock" | "none";
  error: string | null;
}> {
  try {
    const raw = await apiFetch<ApiListing>(`/api/listings/${id}`);
    return { listing: mapApiListing(raw), source: "api", error: null };
  } catch (err) {
    const mock = getMockListingById(id) ?? null;
    if (err instanceof ApiError && err.status === 404) {
      return {
        listing: mock,
        source: mock ? "mock" : "none",
        error: mock ? null : "Listing not found",
      };
    }
    const message =
      err instanceof ApiError
        ? err.message
        : "Could not load listing from the API.";
    return {
      listing: mock,
      source: mock ? "mock" : "none",
      error: message,
    };
  }
}

function extractReviews(payload: unknown): ListingReview[] {
  const list = Array.isArray(payload)
    ? payload
    : payload && typeof payload === "object" && "items" in payload
      ? (payload as { items: unknown[] }).items
      : [];
  const reviews: ListingReview[] = [];
  for (const item of list) {
    if (!item || typeof item !== "object") continue;
    const rec = item as Record<string, unknown>;
    const rating = Number(rec.rating ?? rec.stars ?? 0);
    if (!Number.isFinite(rating) || rating < 1) continue;
    const review: ListingReview = { rating };
    if (rec.id != null) review.id = String(rec.id);
    if (rec.comment != null) review.comment = String(rec.comment);
    else if (rec.body != null) review.comment = String(rec.body);
    if (rec.created_at != null) review.created_at = String(rec.created_at);
    else if (rec.createdAt != null) review.created_at = String(rec.createdAt);
    reviews.push(review);
  }
  return reviews;
}

export async function fetchListingReviews(
  listingId: string,
): Promise<{ reviews: ListingReview[]; error: string | null }> {
  try {
    const result = await apiFetchOptional<unknown>(
      `/api/listings/${listingId}/reviews`,
    );
    if (result.data == null) {
      return { reviews: [], error: null };
    }
    return { reviews: extractReviews(result.data), error: null };
  } catch (err) {
    return {
      reviews: [],
      error:
        err instanceof ApiError
          ? err.message
          : "Could not load reviews.",
    };
  }
}

export async function fetchListingAvailability(
  listingId: string,
  startDate?: string,
  endDate?: string,
): Promise<{ days: AvailabilityDayDto[]; error: string | null }> {
  const from = startDate || isoDate(0);
  const to = endDate || isoDate(19);
  try {
    const data = await apiFetch<{ days?: AvailabilityDayDto[] }>(
      `/api/availability/${listingId}?start_date=${encodeURIComponent(from)}&end_date=${encodeURIComponent(to)}`,
    );
    return { days: data.days ?? [], error: null };
  } catch (err) {
    if (err instanceof ApiError && err.status === 404) {
      return { days: [], error: null };
    }
    return {
      days: [],
      error:
        err instanceof ApiError
          ? err.message
          : "Could not load availability.",
    };
  }
}
