"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Heart, MapPin, MessageSquare, ShoppingCart, Users, Zap } from "lucide-react";
import { CATEGORY_LABELS } from "@marketplays/shared";
import { CISBadge } from "@/components/shared/CISBadge";
import { fetchListingAvailability } from "@/components/buyer/listing-api";
import type { AvailabilityDayDto } from "@/components/buyer/listing-mapper";
import { pinAvailabilityColour } from "@/components/buyer/pin-colour";
import { formatWeeklyPriceFromDailyPence } from "@/components/buyer/price";
import type { BuyerListing, PinAvailability } from "@/components/buyer/types";
import { cn } from "@/lib/utils";

export interface ListingSlideInPanelProps {
  listing: BuyerListing | null;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onBook?: (listing: BuyerListing) => void;
  onMessageSeller?: (listing: BuyerListing) => void;
  inCart?: boolean;
  onToggleCart?: (listing: BuyerListing) => void;
  isFavourite?: boolean;
  onToggleFavourite?: (listing: BuyerListing) => void;
  bookingError?: string | null;
  isBooking?: boolean;
  availabilityFrom?: string;
  availabilityTo?: string;
  readOnly?: boolean;
}

/** Deterministic 20-day strip from listing availability (visual until occupancy API). */
function buildAvailabilityStrip(
  listing: BuyerListing,
): PinAvailability[] {
  const pattern: PinAvailability[] =
    listing.availability === "booked"
      ? ["booked", "booked", "limited", "booked", "available"]
      : listing.availability === "limited"
        ? ["available", "limited", "available", "limited", "booked"]
        : ["available", "available", "limited", "available", "available"];
  return Array.from({ length: 20 }, (_, i) => pattern[i % pattern.length]!);
}

/**
 * Right slide-in 360px (spec §5.4).
 * Single click stays here; full detail is /listings/[id].
 */
export function ListingSlideInPanel({
  listing,
  open,
  onOpenChange,
  onBook,
  onMessageSeller,
  inCart = false,
  onToggleCart,
  isFavourite = false,
  onToggleFavourite,
  bookingError = null,
  isBooking = false,
  availabilityFrom,
  availabilityTo,
  readOnly = false,
}: ListingSlideInPanelProps) {
  const [availDays, setAvailDays] = useState<AvailabilityDayDto[] | null>(null);

  useEffect(() => {
    if (!open || !listing) {
      setAvailDays(null);
      return;
    }
    let cancelled = false;
    void fetchListingAvailability(
      listing.id,
      availabilityFrom,
      availabilityTo,
    ).then((result) => {
      if (cancelled) return;
      setAvailDays(result.days.length > 0 ? result.days : null);
    });
    return () => {
      cancelled = true;
    };
  }, [open, listing?.id, availabilityFrom, availabilityTo]);

  if (!open) return null;

  const strip: PinAvailability[] = availDays
    ? availDays.slice(0, 20).map((d) => (d.is_locked ? "booked" : "available"))
    : listing
      ? buildAvailabilityStrip(listing)
      : [];
  while (strip.length > 0 && strip.length < 20) {
    strip.push("available");
  }

  return (
    <aside
      className={cn(
        "fixed right-0 top-14 z-40 flex h-[calc(100vh-3.5rem)] w-[360px] flex-col border-l border-[#1D2330] bg-[#0A0E16]",
        "shadow-[-12px_0_40px_rgba(0,0,0,0.35)]",
      )}
      aria-label="Listing detail"
    >
      {listing ? (
        <>
          <div className="relative border-b border-[#1D2330]">
            <button
              type="button"
              onClick={() => onOpenChange(false)}
              className="absolute right-3 top-3 z-10 rounded-[8px] border border-[#262C38] bg-[#10141C] px-2 py-1 text-[12px] text-[#9AA3B2] hover:text-white"
            >
              Close
            </button>
            <div
              className="aspect-[16/10] w-full bg-[#171C26]"
              aria-hidden
            />
          </div>

          <div className="flex flex-1 flex-col gap-4 overflow-y-auto p-4 pb-28">
            <div>
              <h2 className="pr-16 text-[17px] font-bold leading-snug text-[#F5F6F8]">
                {listing.title}
              </h2>
              <p className="mt-1 text-[13px] text-[#9AA3B2]">
                {CATEGORY_LABELS[listing.category]} · {listing.city}
              </p>
              <div className="mt-2">
                <CISBadge score={listing.cisScore} />
              </div>
            </div>

            <div>
              <p className="text-[24px] font-bold tracking-tight text-[#F5F6F8]">
                {formatWeeklyPriceFromDailyPence(listing.pricePerDayPence)}
              </p>
              <p className="text-[12px] text-[#6B7280]">weekly rate</p>
            </div>

            <p className="text-[13px] leading-relaxed text-[#9AA3B2]">
              {listing.description}
            </p>

            <div className="space-y-2 text-[13px]">
              <div className="flex items-center gap-2 text-[#9AA3B2]">
                <MapPin className="size-4 shrink-0 text-[#6B7280]" />
                <span>
                  {listing.addressLine1}, {listing.postcode}
                </span>
              </div>
              <div className="flex items-center gap-2 text-[#9AA3B2]">
                <Users className="size-4 shrink-0 text-[#6B7280]" />
                <span>
                  ~{listing.audienceSize.toLocaleString("en-GB")} weekly reach
                </span>
              </div>
            </div>

            <div className="flex flex-wrap gap-1.5">
              {listing.audienceTags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-[20px] border border-[#262C38] bg-[#171C26] px-2.5 py-0.5 text-[12px] text-[#9AA3B2]"
                >
                  {tag}
                </span>
              ))}
            </div>

            <div>
              <p className="mb-2 text-[12.5px] font-semibold uppercase tracking-[0.04em] text-[#9AA3B2]">
                Next 20 days
              </p>
              <div className="grid grid-cols-10 gap-1">
                {strip.map((day, idx) => (
                  <span
                    key={idx}
                    className="h-2.5 rounded-sm"
                    style={{ backgroundColor: pinAvailabilityColour(day) }}
                    title={day}
                  />
                ))}
              </div>
            </div>

            {!readOnly && (
              <>
                <button
                  type="button"
                  onClick={() => onToggleFavourite?.(listing)}
                  className={cn(
                    "flex w-full items-center justify-center gap-2 rounded-[9px] border px-3 py-2.5 text-[13px] font-semibold transition-colors",
                    isFavourite
                      ? "border-[#3B5BFF] bg-[#3B5BFF]/20 text-[#F5F6F8]"
                      : "border-[#262C38] bg-[#171C26] text-[#F5F6F8] hover:border-[#3B5BFF]",
                  )}
                >
                  <Heart className="size-4" />
                  {isFavourite ? "Saved to favourites" : "Save to favourites"}
                </button>
                <button
                  type="button"
                  onClick={() => onToggleCart?.(listing)}
                  disabled={listing.availability === "booked"}
                  className={cn(
                    "flex w-full items-center justify-center gap-2 rounded-[9px] border px-3 py-2.5 text-[13px] font-semibold transition-colors disabled:opacity-40",
                    inCart
                      ? "border-[#5C1F1F] bg-[#301414] text-[#F1544B]"
                      : "border-[#262C38] bg-[#171C26] text-[#F5F6F8] hover:border-[#3B5BFF]",
                  )}
                >
                  <ShoppingCart className="size-4" />
                  {inCart ? "Remove from campaign cart" : "Add to campaign cart"}
                </button>
              </>
            )}

            <Link
              href={`/listings/${listing.id}`}
              className="text-center text-[12.5px] text-[#3B5BFF] hover:underline"
            >
              View full listing
            </Link>
          </div>

          {!readOnly && (
            <div className="absolute inset-x-0 bottom-0 flex flex-col gap-2 border-t border-[#1D2330] bg-[#0A0E16] p-4">
              {bookingError ? (
                <p className="text-[12.5px] text-[#F1544B]" role="alert">
                  {bookingError}
                </p>
              ) : null}
              <div className="flex gap-2">
                <button
                  type="button"
                  disabled={listing.availability === "booked" || isBooking}
                  onClick={() => onBook?.(listing)}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-[9px] bg-[#3B5BFF] px-3 py-2.5 text-[13px] font-semibold text-white disabled:opacity-40"
                >
                  <Zap className="size-4" />
                  {isBooking ? "Booking…" : "Instant book"}
                </button>
                <button
                  type="button"
                  onClick={() => onMessageSeller?.(listing)}
                  className="flex flex-1 items-center justify-center gap-1.5 rounded-[9px] border border-[#262C38] bg-[#171C26] px-3 py-2.5 text-[13px] font-semibold text-[#F5F6F8]"
                >
                  <MessageSquare className="size-4" />
                  Message seller
                </button>
              </div>
            </div>
          )}
        </>
      ) : null}
    </aside>
  );
}
