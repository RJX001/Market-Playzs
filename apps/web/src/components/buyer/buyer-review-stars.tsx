"use client";

import { useState } from "react";
import { apiFetch, ApiError } from "@/components/buyer/api-client";

export interface BuyerReviewStarsProps {
  bookingId: string;
  onSubmitted?: () => void;
  className?: string;
}

/** Star prompt for Awaiting_Buyer_Review → POST /api/bookings/{id}/review */
export function BuyerReviewStars({
  bookingId,
  onSubmitted,
  className,
}: BuyerReviewStarsProps) {
  const [hovered, setHovered] = useState(0);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(rating: number): Promise<void> {
    if (busy || done) return;
    setBusy(true);
    setError(null);
    try {
      await apiFetch(`/api/bookings/${bookingId}/review`, {
        method: "POST",
        auth: true,
        body: JSON.stringify({
          rating,
          delivery_score: 1,
          comment: null,
        }),
      });
      setDone(true);
      onSubmitted?.();
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.status === 404
            ? "Review API returned 404 — review was not saved."
            : err.message
          : "Could not submit review.",
      );
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return (
      <p className={className ?? "text-[12.5px] text-[#34D399]"}>
        Review submitted.
      </p>
    );
  }

  return (
    <div className={className}>
      <p className="mb-1 text-[12.5px] text-[#9AA3B2]">Rate this campaign</p>
      <div className="flex items-center gap-1">
        {[1, 2, 3, 4, 5].map((n) => (
          <button
            key={n}
            type="button"
            disabled={busy}
            aria-label={`Rate ${n} of 5`}
            onMouseEnter={() => setHovered(n)}
            onMouseLeave={() => setHovered(0)}
            onClick={() => void submit(n)}
            className="text-[16px] leading-none disabled:opacity-40"
            style={{ color: n <= hovered ? "#F5A623" : "#6B7280" }}
          >
            ★
          </button>
        ))}
      </div>
      {error ? (
        <p className="mt-1 text-[12px] text-[#F1544B]">{error}</p>
      ) : null}
    </div>
  );
}
