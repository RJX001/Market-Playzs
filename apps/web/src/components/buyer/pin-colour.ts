import { BuyerToken } from "@/components/buyer/buyer-tokens";
import type { BuyerListing, PinAvailability } from "@/components/buyer/types";

const AVAILABILITY_COLOUR: Record<PinAvailability, string> = {
  available: BuyerToken.pinAvailable,
  limited: BuyerToken.pinLimited,
  booked: BuyerToken.pinBooked,
};

/** Pin fill from availability only (spec §2.4). Selection is a blue ring, not a fill swap. */
export function resolvePinColour(listing: BuyerListing): string {
  return AVAILABILITY_COLOUR[listing.availability];
}

export function pinAvailabilityColour(availability: PinAvailability): string {
  return AVAILABILITY_COLOUR[availability];
}
