import type { BuyerFilterState, BuyerListing } from "@/components/buyer/types";
import { weeklyPoundsFromDailyPence } from "@/components/buyer/price";

/** Apply sidebar filters locally against mock (or future API) listings. */
export function filterListings(
  listings: BuyerListing[],
  filters: BuyerFilterState,
): BuyerListing[] {
  return listings.filter((listing) => {
    if (
      filters.assetTypes.length > 0 &&
      !filters.assetTypes.includes(listing.category)
    ) {
      return false;
    }

    if (
      filters.audience.length > 0 &&
      !filters.audience.some((tag) => listing.audienceTags.includes(tag))
    ) {
      return false;
    }

    if (filters.priceMaxWeek !== null) {
      const week = weeklyPoundsFromDailyPence(listing.pricePerDayPence);
      if (week > filters.priceMaxWeek) return false;
    }

    if (filters.cisMin !== null) {
      // Null CIS ("New") included in all CIS tiers (Section 5.4 / filter rules).
      if (listing.cisScore !== null && listing.cisScore < filters.cisMin) {
        return false;
      }
    }

    if (
      filters.bookingType !== "all" &&
      listing.bookingType !== filters.bookingType
    ) {
      return false;
    }

    return true;
  });
}
