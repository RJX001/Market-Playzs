/** Exact category enum from Section 1.3 — single shared source for FE/BE/DB. */
export const Category = {
  sports_club: "sports_club",
  gym: "gym",
  school: "school",
  shop: "shop",
  cafe: "cafe",
  festival: "festival",
  community_event: "community_event",
  billboard: "billboard",
  event_venue: "event_venue",
} as const;

export type Category = (typeof Category)[keyof typeof Category];

export const CATEGORY_VALUES: readonly Category[] = Object.values(Category);

export const CATEGORY_LABELS: Record<Category, string> = {
  sports_club: "Sports Club",
  gym: "Gym",
  school: "School",
  shop: "Shop",
  cafe: "Café",
  festival: "Festival",
  community_event: "Community Event",
  billboard: "Billboard",
  event_venue: "Event Venue",
};

export function isCategory(value: string): value is Category {
  return (CATEGORY_VALUES as readonly string[]).includes(value);
}
