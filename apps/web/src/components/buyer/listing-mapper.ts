import type { Category } from "@marketplays/shared";
import type {
  BookingType,
  BuyerFilterState,
  BuyerListing,
  MapBBox,
  PinAvailability,
} from "@/components/buyer/types";

const LONDON_CENTER = { lng: -0.09, lat: 51.52 };

const CATEGORIES = new Set<string>([
  "sports_club",
  "gym",
  "school",
  "shop",
  "cafe",
  "festival",
  "community_event",
  "billboard",
  "event_venue",
]);

export interface ApiListing {
  id: string;
  title?: string;
  description?: string;
  category?: string;
  city?: string;
  postcode?: string;
  address_line1?: string;
  addressLine1?: string;
  lat?: number;
  lng?: number;
  price_per_day_pence?: number;
  pricePerDayPence?: number;
  cis_score?: number | null;
  cisScore?: number | null;
  audience_size?: number;
  audienceSize?: number;
  audience_tags?: string[];
  audienceTags?: string[];
  booking_types?: string[];
  bookingTypes?: string[];
  images?: string[];
  imageUrls?: string[];
  availability?: string;
}

export interface ListingSearchResponse {
  items: ApiListing[];
  total: number;
  page: number;
  page_size: number;
}

export interface AvailabilityDayDto {
  day: string;
  is_locked: boolean;
  booking_id?: string | null;
}

function asStringArray(value: unknown): string[] {
  if (!Array.isArray(value)) return [];
  return value.map((item) => String(item));
}

function asCategory(value: unknown): Category {
  const raw = String(value ?? "shop");
  return (CATEGORIES.has(raw) ? raw : "shop") as Category;
}

function asBookingType(types: string[]): BookingType {
  return types.includes("instant") ? "instant" : "request";
}

function asAvailability(value: unknown): PinAvailability {
  if (value === "limited" || value === "booked" || value === "available") {
    return value;
  }
  return "available";
}

export function mapApiListing(raw: ApiListing): BuyerListing {
  const bookingTypes = asStringArray(raw.booking_types ?? raw.bookingTypes);
  return {
    id: String(raw.id),
    title: String(raw.title ?? "Untitled space"),
    description: String(raw.description ?? ""),
    category: asCategory(raw.category),
    city: String(raw.city ?? ""),
    postcode: String(raw.postcode ?? ""),
    addressLine1: String(raw.address_line1 ?? raw.addressLine1 ?? ""),
    lat: Number(raw.lat ?? 0),
    lng: Number(raw.lng ?? 0),
    pricePerDayPence: Number(
      raw.price_per_day_pence ?? raw.pricePerDayPence ?? 0,
    ),
    cisScore:
      raw.cis_score == null && raw.cisScore == null
        ? null
        : Number(raw.cis_score ?? raw.cisScore),
    audienceSize: Number(raw.audience_size ?? raw.audienceSize ?? 0),
    audienceTags: asStringArray(raw.audience_tags ?? raw.audienceTags),
    bookingType: asBookingType(bookingTypes),
    availability: asAvailability(raw.availability),
    imageUrls: asStringArray(raw.images ?? raw.imageUrls),
  };
}

export function availabilityFromDays(
  days: AvailabilityDayDto[],
): PinAvailability {
  if (days.length === 0) return "available";
  const locked = days.filter((d) => d.is_locked).length;
  if (locked === days.length) return "booked";
  if (locked > 0) return "limited";
  return "available";
}

/** Weekly £ max → daily pence (listings store integer pence / day). */
function weeklyPoundsToDailyPence(weeklyPounds: number): number {
  return Math.round((weeklyPounds * 100) / 7);
}

export function listingsQueryFromFilters(
  filters: BuyerFilterState,
  bbox?: MapBBox | null,
): string {
  const params = new URLSearchParams();
  params.set("page", "1");
  params.set("page_size", "20");
  params.set("include_new_cis", "true");
  params.set("radius_km", String(Math.min(10, Math.max(1, filters.radiusKm))));

  if (bbox) {
    params.set("min_lng", String(bbox.west));
    params.set("min_lat", String(bbox.south));
    params.set("max_lng", String(bbox.east));
    params.set("max_lat", String(bbox.north));
    params.set("center_lng", String((bbox.west + bbox.east) / 2));
    params.set("center_lat", String((bbox.south + bbox.north) / 2));
  } else {
    params.set("center_lng", String(LONDON_CENTER.lng));
    params.set("center_lat", String(LONDON_CENTER.lat));
  }

  for (const category of filters.assetTypes) {
    params.append("categories", category);
  }
  for (const tag of filters.audience) {
    params.append("audience", tag);
  }
  if (filters.bookingType !== "all") {
    params.append("booking_types", filters.bookingType);
  }
  if (filters.priceMaxWeek !== null && Number.isFinite(filters.priceMaxWeek)) {
    params.set(
      "price_max_pence",
      String(weeklyPoundsToDailyPence(filters.priceMaxWeek)),
    );
  }
  if (filters.cisMin !== null) {
    params.set("cis_min", String(filters.cisMin));
  }
  if (filters.availabilityFrom) {
    params.set("available_from", filters.availabilityFrom);
  }
  if (filters.availabilityTo) {
    params.set("available_to", filters.availabilityTo);
  }

  return params.toString();
}

export function isoDate(offsetDays = 0): string {
  const d = new Date();
  d.setDate(d.getDate() + offsetDays);
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}
