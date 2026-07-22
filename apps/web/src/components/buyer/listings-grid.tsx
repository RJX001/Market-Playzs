"use client";

import { CATEGORY_LABELS } from "@marketplays/shared";
import { CISBadge } from "@/components/shared/CISBadge";
import { formatWeeklyPriceFromDailyPence } from "@/components/buyer/price";
import type { BuyerListing } from "@/components/buyer/types";
import { cn } from "@/lib/utils";

export interface ListingsGridProps {
  listings: BuyerListing[];
  selectedId: string | null;
  onSelect: (listingId: string) => void;
  className?: string;
}

export function ListingsGrid({
  listings,
  selectedId,
  onSelect,
  className,
}: ListingsGridProps) {
  if (listings.length === 0) {
    return (
      <div
        className={cn(
          "flex h-full items-center justify-center bg-[#05070C] text-[14px] text-[#6B7280]",
          className,
        )}
      >
        No spaces match these filters.
      </div>
    );
  }

  return (
    <div
      className={cn(
        "h-full overflow-y-auto bg-[#05070C] p-4",
        className,
      )}
    >
      <div className="grid grid-cols-[repeat(auto-fill,minmax(260px,1fr))] gap-4">
        {listings.map((listing) => {
          const selected = selectedId === listing.id;
          return (
            <button
              key={listing.id}
              type="button"
              onClick={() => onSelect(listing.id)}
              className={cn(
                "overflow-hidden rounded-[14px] border bg-[#10141C] text-left transition-colors",
                selected
                  ? "border-[#3B5BFF]"
                  : "border-[#262C38] hover:border-[#3B5BFF]/50",
              )}
            >
              <div className="aspect-[16/10] bg-[#171C26]" aria-hidden />
              <div className="space-y-2 p-[18px]">
                <div className="flex items-start justify-between gap-2">
                  <h3 className="text-[15px] font-semibold leading-snug text-[#F5F6F8]">
                    {listing.title}
                  </h3>
                  <CISBadge score={listing.cisScore} />
                </div>
                <p className="text-[12.5px] text-[#9AA3B2]">
                  {CATEGORY_LABELS[listing.category]} · {listing.city}
                </p>
                <p className="text-[15px] font-bold text-[#F5F6F8]">
                  {formatWeeklyPriceFromDailyPence(listing.pricePerDayPence)}
                </p>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
