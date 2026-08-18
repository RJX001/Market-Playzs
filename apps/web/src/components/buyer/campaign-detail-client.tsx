"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  BOOKING_STATUS_LABELS,
  BookingStatus,
  isBookingStatus,
  penceToPoundsDisplay,
} from "@marketplays/shared";
import { BuyerReviewStars } from "@/components/buyer/buyer-review-stars";
import {
  fetchBuyerBooking,
  type BuyerBooking,
} from "@/components/buyer/campaigns-api";
import { buttonVariants } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

function formatDay(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function CampaignDetailClient({ id }: { id: string }) {
  const [booking, setBooking] = useState<BuyerBooking | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const result = await fetchBuyerBooking(id);
    if (!result.ok) {
      setError(result.error);
      setBooking(null);
    } else {
      setError(null);
      setBooking(result.booking);
    }
    setLoading(false);
  }, [id]);

  useEffect(() => {
    void load();
  }, [load]);

  const statusLabel =
    booking && isBookingStatus(booking.status)
      ? BOOKING_STATUS_LABELS[booking.status]
      : booking?.status ?? "";

  return (
    <div className="mx-auto max-w-3xl px-4 py-10">
      <p className="text-xs text-muted-foreground">Campaign</p>
      <h1 className="mt-1 text-2xl font-semibold tracking-tight text-foreground">
        {booking?.listing_title || id}
      </h1>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>
            {loading ? "Loading booking…" : error ? "Could not load booking" : "Booking"}
          </CardTitle>
          <CardDescription>
            {error
              ? error
              : booking
                ? `${statusLabel} · ${formatDay(booking.start_date)} – ${formatDay(booking.end_date)}`
                : "Full timeline, deliverables, and review actions."}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {booking ? (
            <div className="space-y-1 text-sm">
              <p>Status: {statusLabel}</p>
              <p>Total: {penceToPoundsDisplay(booking.total_pence)}</p>
              {booking.rating != null ? <p>Your rating: {booking.rating}/5</p> : null}
              {booking.status === BookingStatus.Awaiting_Buyer_Review ? (
                <BuyerReviewStars bookingId={booking.id} onSubmitted={() => void load()} />
              ) : null}
            </div>
          ) : null}
          <div className="flex flex-wrap gap-2">
            <Link
              href="/campaigns"
              className={cn(buttonVariants({ variant: "outline" }))}
            >
              Back to campaigns
            </Link>
            <Link href="/map" className={cn(buttonVariants())}>
              Explore map
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
