"use client";

import { useCallback, useState } from "react";
import { apiFetch, ApiError } from "@/components/buyer/api-client";
import type { BuyerListing } from "@/components/buyer/types";

export interface BookingDraft {
  listingId: string;
  startDate: string;
  endDate: string;
  paymentMethod?: "card" | "invoice";
  bookingId?: string;
  clientSecret?: string;
  status?: string;
  totalPence?: number;
}

export type BookingOk = { ok: true; draft: BookingDraft };
export type BookingFail = { ok: false; error: string };

export interface UseBookingResult {
  isSubmitting: boolean;
  error: string | null;
  lastDraft: BookingDraft | null;
  startBooking: (
    listing: BuyerListing,
    startDate: string,
    endDate: string,
    options?: { paymentMethod?: "card" | "invoice" },
  ) => Promise<BookingOk | BookingFail>;
  startCampaignBookings: (
    listings: BuyerListing[],
    startDate: string,
    endDate: string,
    paymentMethod: "card" | "invoice",
  ) => Promise<
    | { ok: true; bookedCount: number; drafts: BookingDraft[] }
    | { ok: false; error: string; bookedCount: number }
  >;
  submitReview: (
    bookingId: string,
    rating: number,
    options?: { deliveryScore?: 0 | 0.5 | 1; comment?: string },
  ) => Promise<{ ok: true } | { ok: false; error: string }>;
  clearError: () => void;
}

interface BookingCreateResponse {
  booking_id?: string;
  bookingId?: string;
  client_secret?: string;
  clientSecret?: string;
  status?: string;
  total_pence?: number;
  totalPence?: number;
}

async function postBooking(draft: BookingDraft): Promise<BookingDraft> {
  const body = await apiFetch<BookingCreateResponse>("/api/bookings", {
    method: "POST",
    auth: true,
    body: JSON.stringify({
      listing_id: draft.listingId,
      start_date: draft.startDate,
      end_date: draft.endDate,
    }),
  });
  const clientSecret = body.client_secret ?? body.clientSecret;
  return {
    ...draft,
    bookingId: body.booking_id ?? body.bookingId,
    clientSecret,
    status: body.status,
    totalPence: body.total_pence ?? body.totalPence,
  };
}

function validateBooking(
  listing: BuyerListing,
  startDate: string,
  endDate: string,
): string | null {
  if (listing.availability === "booked") {
    return "This space is fully booked for the selected window.";
  }
  if (!startDate || !endDate || startDate > endDate) {
    return "Choose a valid availability window.";
  }
  return null;
}

function toErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 401) return "Log in to complete a booking.";
    if (err.status === 404) {
      return "Booking API returned 404 — booking was not created.";
    }
    return err.message;
  }
  return "Booking failed.";
}

/**
 * Buyer booking helper — POST /api/bookings.
 * 404 is an error (never treated as success). Money stays in pence.
 */
export function useBooking(): UseBookingResult {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastDraft, setLastDraft] = useState<BookingDraft | null>(null);

  const clearError = useCallback(() => setError(null), []);

  const createDraft = useCallback(
    async (
      listing: BuyerListing,
      startDate: string,
      endDate: string,
      paymentMethod?: "card" | "invoice",
    ): Promise<BookingOk | BookingFail> => {
      const validationError = validateBooking(listing, startDate, endDate);
      if (validationError) {
        return { ok: false, error: validationError };
      }
      const draft: BookingDraft = {
        listingId: listing.id,
        startDate,
        endDate,
        paymentMethod,
      };
      try {
        const posted = await postBooking(draft);
        return { ok: true, draft: posted };
      } catch (err) {
        return { ok: false, error: toErrorMessage(err) };
      }
    },
    [],
  );

  const startBooking = useCallback(
    async (
      listing: BuyerListing,
      startDate: string,
      endDate: string,
      options?: { paymentMethod?: "card" | "invoice" },
    ): Promise<BookingOk | BookingFail> => {
      setIsSubmitting(true);
      setError(null);
      try {
        const result = await createDraft(
          listing,
          startDate,
          endDate,
          options?.paymentMethod,
        );
        if (!result.ok) {
          setError(result.error);
          return result;
        }
        setLastDraft(result.draft);
        return result;
      } finally {
        setIsSubmitting(false);
      }
    },
    [createDraft],
  );

  const startCampaignBookings = useCallback(
    async (
      listings: BuyerListing[],
      startDate: string,
      endDate: string,
      paymentMethod: "card" | "invoice",
    ) => {
      setIsSubmitting(true);
      setError(null);
      const drafts: BookingDraft[] = [];
      try {
        if (listings.length === 0) {
          const message = "Your cart is empty.";
          setError(message);
          return { ok: false as const, error: message, bookedCount: 0 };
        }
        for (const listing of listings) {
          const result = await createDraft(
            listing,
            startDate,
            endDate,
            paymentMethod,
          );
          if (!result.ok) {
            setError(result.error);
            return {
              ok: false as const,
              error: result.error,
              bookedCount: drafts.length,
            };
          }
          drafts.push(result.draft);
          setLastDraft(result.draft);
        }
        return { ok: true as const, bookedCount: drafts.length, drafts };
      } finally {
        setIsSubmitting(false);
      }
    },
    [createDraft],
  );

  const submitReview = useCallback(
    async (
      bookingId: string,
      rating: number,
      options?: { deliveryScore?: 0 | 0.5 | 1; comment?: string },
    ) => {
      setError(null);
      try {
        await apiFetch(`/api/bookings/${bookingId}/review`, {
          method: "POST",
          auth: true,
          body: JSON.stringify({
            rating,
            delivery_score: options?.deliveryScore ?? 1,
            comment: options?.comment ?? null,
          }),
        });
        return { ok: true as const };
      } catch (err) {
        const message = toErrorMessage(err);
        setError(message);
        return { ok: false as const, error: message };
      }
    },
    [],
  );

  return {
    isSubmitting,
    error,
    lastDraft,
    startBooking,
    startCampaignBookings,
    submitReview,
    clearError,
  };
}
