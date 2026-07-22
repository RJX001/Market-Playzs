import type { Category } from "@marketplays/shared";

export type PinAvailability = "available" | "limited" | "booked";
export type BookingType = "instant" | "request";

export interface BuyerListing {
  id: string;
  title: string;
  description: string;
  category: Category;
  city: string;
  postcode: string;
  addressLine1: string;
  lat: number;
  lng: number;
  /** Integer pence per day (DB convention). */
  pricePerDayPence: number;
  cisScore: number | null;
  audienceSize: number;
  audienceTags: string[];
  bookingType: BookingType;
  availability: PinAvailability;
  imageUrls: string[];
}

export interface MapBBox {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface BuyerFilterState {
  location: string;
  radiusKm: number;
  assetTypes: Category[];
  audience: string[];
  /** Max weekly price in pounds; null = no max. */
  priceMaxWeek: number | null;
  availabilityFrom: string;
  availabilityTo: string;
  cisMin: number | null;
  bookingType: "all" | BookingType;
}
