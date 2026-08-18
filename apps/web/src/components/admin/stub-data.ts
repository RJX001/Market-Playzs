/** Stub platform data for admin UI — replace with API responses. */

export interface AdminDispute {
  id: string;
  bookingId: string;
  listingTitle: string;
  buyerName: string;
  sellerName: string;
  /** Booking amount in pence */
  amountPence: number;
  reason: string;
  openedAt: string;
  status: "open" | "resolved";
  /** B10 SLA: 72h countdown from dispute creation */
  firstDecisionDueAt?: string;
}

export interface AdminUser {
  id: string;
  email: string;
  name: string;
  role: "buyer" | "seller" | "admin";
  status: "active" | "suspended";
  createdAt: string;
}

export interface AdminListing {
  id: string;
  title: string;
  sellerName: string;
  category: string;
  /** null = New */
  cisScore: number | null;
  isCisOverridden: boolean;
  status: "live" | "draft" | "suspended";
  /** Admin-only — never surface to seller UI */
  suspensionReason: string | null;
}

export const STUB_HEALTH = {
  /** GMV in pence (30-day stub) */
  gmvPence: 1_284_500,
  activeListings: 148,
  pendingModeration: 4,
  disputesOpen: 3,
  /** Kept for listings tools page */
  listingsSuspended: 2,
} as const;

export interface ModerationQueueItem {
  id: string;
  title: string;
  sellerName: string;
  category: string;
  submittedAt: string;
}

/** Listings awaiting Approve / Reject (Section 14). */
export const STUB_MODERATION_QUEUE: ModerationQueueItem[] = [
  {
    id: "mod_01",
    title: "Festival stage wrap — Harbour Lights",
    sellerName: "Harbour Events CIC",
    category: "festival",
    submittedAt: "2026-07-21T08:30:00Z",
  },
  {
    id: "mod_02",
    title: "School playground fence — Maple Juniors",
    sellerName: "Maple PTA",
    category: "school",
    submittedAt: "2026-07-21T11:15:00Z",
  },
  {
    id: "mod_03",
    title: "High street A-board — Corner Shop",
    sellerName: "Corner Shop Ltd",
    category: "shop",
    submittedAt: "2026-07-22T07:45:00Z",
  },
  {
    id: "mod_04",
    title: "Community hall entrance screen",
    sellerName: "Westfield Community Trust",
    category: "community_event",
    submittedAt: "2026-07-22T09:05:00Z",
  },
];

export const STUB_DISPUTES: AdminDispute[] = [
  {
    id: "dsp_01",
    bookingId: "bk_901",
    listingTitle: "Pitchside banner — Riverside FC",
    buyerName: "Northstar Agency",
    sellerName: "Riverside FC",
    amountPence: 45000,
    reason: "Buyer reports proof video does not show agreed placement.",
    openedAt: "2026-07-18T09:12:00Z",
    status: "open",
  },
  {
    id: "dsp_02",
    bookingId: "bk_874",
    listingTitle: "Gym entrance screen — Pulse Fitness",
    buyerName: "Cafe Co.",
    sellerName: "Pulse Fitness Ltd",
    amountPence: 28000,
    reason: "Creative not displayed for full campaign window.",
    openedAt: "2026-07-19T14:40:00Z",
    status: "open",
  },
  {
    id: "dsp_03",
    bookingId: "bk_812",
    listingTitle: "Café window vinyl — Bean & Co",
    buyerName: "Local Bank PLC",
    sellerName: "Bean & Co",
    amountPence: 12000,
    reason: "Seller missed Awaiting_Proof deadline; buyer reported issue.",
    openedAt: "2026-07-20T11:05:00Z",
    status: "open",
  },
];

export const STUB_USERS: AdminUser[] = [
  {
    id: "usr_b1",
    email: "maya@northstar.agency",
    name: "Maya Chen",
    role: "buyer",
    status: "active",
    createdAt: "2026-03-12",
  },
  {
    id: "usr_s1",
    email: "ops@riversidefc.co.uk",
    name: "Tom Hale",
    role: "seller",
    status: "active",
    createdAt: "2026-02-01",
  },
  {
    id: "usr_s2",
    email: "hello@pulsefitness.co.uk",
    name: "Sara Quinn",
    role: "seller",
    status: "suspended",
    createdAt: "2026-01-20",
  },
  {
    id: "usr_b2",
    email: "ads@cafeco.com",
    name: "Jordan Lee",
    role: "buyer",
    status: "active",
    createdAt: "2026-04-08",
  },
];

export const STUB_LISTINGS: AdminListing[] = [
  {
    id: "lst_01",
    title: "Pitchside banner — Riverside FC",
    sellerName: "Riverside FC",
    category: "sports_club",
    cisScore: 92,
    isCisOverridden: false,
    status: "live",
    suspensionReason: null,
  },
  {
    id: "lst_02",
    title: "Gym entrance screen — Pulse Fitness",
    sellerName: "Pulse Fitness Ltd",
    category: "gym",
    cisScore: 61,
    isCisOverridden: true,
    status: "suspended",
    suspensionReason:
      "Repeated proof delivery failures; buyer complaints across 3 bookings.",
  },
  {
    id: "lst_03",
    title: "School fence wrap — Oakwood Primary",
    sellerName: "Oakwood PTA",
    category: "school",
    cisScore: null,
    isCisOverridden: false,
    status: "live",
    suspensionReason: null,
  },
  {
    id: "lst_04",
    title: "High street billboard — Station Rd",
    sellerName: "Urban Media Co",
    category: "billboard",
    cisScore: 44,
    isCisOverridden: false,
    status: "suspended",
    suspensionReason: "Policy violation: prohibited category creative shown.",
  },
];
