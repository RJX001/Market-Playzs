/** Shared route constants for portal chrome (buyer ↔ seller ↔ admin). */
export const ROUTES = {
  home: "/",
  buyerMap: "/map",
  buyerCampaigns: "/campaigns",
  bookings: "/bookings",
  messages: "/messages",
  sellerDashboard: "/dashboard",
  sellerListings: "/listings",
  admin: "/admin",
  login: "/auth/login",
  register: "/auth/register",
} as const;

export type AppRoute = (typeof ROUTES)[keyof typeof ROUTES];

/** Section 4 role nav — used by portal layouts. */
export const BUYER_NAV = [
  { href: ROUTES.buyerMap, label: "Explore map" },
  { href: ROUTES.buyerCampaigns, label: "My campaigns" },
  { href: ROUTES.bookings, label: "Bookings" },
  { href: ROUTES.messages, label: "Messages" },
] as const;

export const SELLER_NAV = [
  { href: ROUTES.sellerDashboard, label: "Dashboard" },
  { href: ROUTES.sellerListings, label: "My listings" },
  { href: ROUTES.bookings, label: "Bookings" },
  { href: ROUTES.messages, label: "Messages" },
] as const;

export const ADMIN_NAV = [{ href: ROUTES.admin, label: "Admin" }] as const;
