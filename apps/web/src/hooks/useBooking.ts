"use client";

import { useCallback, useState } from "react";
import type { BuyerListing } from "@/components/buyer/types";

export interface BookingDraft {
  listingId: string;
  startDate: string;
  endDate: string;
  paymentMethod?: "card" | "invoice";
}

export interface UseBookingResult {
  isSubmitting: boolean;
  error: string | null;
  lastDraft: BookingDraft | null;
  /** Creates a booking via POST /api/bookings when present; otherwise keeps a local draft. */
  startBooking: (
    listing: BuyerListing,
    startDate: string,
    endDate: string,
    options?: { paymentMethod?: "card" | "invoice" },
  ) => Promise<{ ok: true; draft: BookingDraft } | { ok: false; error: string }>;
  /** Multi-space campaign checkout — one booking request per cart item. */
  startCampaignBookings: (
    listings: BuyerListing[],
    startDate: string,
    endDate: string,
    paymentMethod: "card" | "invoice",
  ) => Promise<
    | { ok: true; bookedCount: number; drafts: BookingDraft[] }
    | { ok: false; error: string; bookedCount: number }
  >;
  clearError: () => void;
}

async function postBookingIfAvailable(
  draft: BookingDraft,
): Promise<{ ok: boolean; error?: string }> {
  try {
    const res = await fetch("/api/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        listing_id: draft.listingId,
        start_date: draft.startDate,
        end_date: draft.endDate,
        payment_method: draft.paymentMethod ?? "card",
      }),
    });
    // Endpoint missing (404) or not ready — treat as client-side success with draft.
    if (res.status === 404 || res.status === 501) {
      return { ok: true };
    }
    if (!res.ok) {
      let message = `Booking failed (${res.status})`;
      try {
        const body = (await res.json()) as { detail?: string; error?: string };
        message = body.detail ?? body.error ?? message;
      } catch {
        /* ignore parse */
      }
      return { ok: false, error: message };
    }
    return { ok: true };
  } catch {
    // Network / no route — keep draft-only success for local UX.
    return { ok: true };
  }
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

/**
 * Buyer booking helper — wires to POST /api/bookings when the API ships.
 * Money remains in pence; UI formats at the edge.
 * Does not invent schemas or change booking status enums.
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
    ): Promise<
      { ok: true; draft: BookingDraft } | { ok: false; error: string }
    > => {
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
      const posted = await postBookingIfAvailable(draft);
      if (!posted.ok) {
        return { ok: false, error: posted.error ?? "Booking failed." };
      }
      return { ok: true, draft };
    },
    [],
  );

  const startBooking = useCallback(
    async (
      listing: BuyerListing,
      startDate: string,
      endDate: string,
      options?: { paymentMethod?: "card" | "invoice" },
    ): Promise<
      { ok: true; draft: BookingDraft } | { ok: false; error: string }
    > => {
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

  return {
    isSubmitting,
    error,
    lastDraft,
    startBooking,
    startCampaignBookings,
    clearError,
  };
}
