"use client";

import { useState } from "react";
import Link from "next/link";
import { useBooking } from "@/hooks/useBooking";
import { useFavourites } from "@/components/buyer/use-favourites";
import {
  StripePaymentForm,
  stripePublishableKey,
} from "@/components/buyer/stripe-payment-form";
import type { BuyerListing } from "@/components/buyer/types";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export function ListingDetailActions({
  listing,
  startDate,
  endDate,
}: {
  listing: BuyerListing;
  startDate: string;
  endDate: string;
}) {
  const { startBooking, isSubmitting, error } = useBooking();
  const { isFavourite, toggle, error: favError } = useFavourites();
  const [clientSecret, setClientSecret] = useState<string | null>(null);
  const [paid, setPaid] = useState(false);
  const [payError, setPayError] = useState<string | null>(null);

  const favourite = isFavourite(listing.id);

  return (
    <div className="mt-6 space-y-3">
      {clientSecret && stripePublishableKey() && !paid ? (
        <StripePaymentForm
          clientSecret={clientSecret}
          onPaid={() => setPaid(true)}
          onError={setPayError}
        />
      ) : (
        <button
          type="button"
          disabled={listing.availability === "booked" || isSubmitting || paid}
          onClick={() => {
            void startBooking(listing, startDate, endDate).then((result) => {
              if (!result.ok) return;
              if (result.draft.clientSecret && stripePublishableKey()) {
                setClientSecret(result.draft.clientSecret);
              } else {
                setPaid(true);
              }
            });
          }}
          className={cn(buttonVariants({ size: "lg" }), "w-full")}
        >
          {paid
            ? "Booking created"
            : isSubmitting
              ? "Booking…"
              : listing.bookingType === "instant"
                ? "Instant book"
                : "Request to book"}
        </button>
      )}
      <button
        type="button"
        onClick={() => void toggle(listing.id)}
        className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}
      >
        {favourite ? "Saved to favourites" : "Save to favourites"}
      </button>
      <Link
        href="/map"
        className={cn(buttonVariants({ variant: "outline", size: "lg" }), "w-full")}
      >
        Back to map
      </Link>
      {error ? (
        <p className="text-sm text-red-600" role="alert">
          {error}
        </p>
      ) : null}
      {payError ? (
        <p className="text-sm text-red-600" role="alert">
          {payError}
        </p>
      ) : null}
      {favError ? (
        <p className="text-sm text-red-600" role="alert">
          {favError}
        </p>
      ) : null}
    </div>
  );
}
