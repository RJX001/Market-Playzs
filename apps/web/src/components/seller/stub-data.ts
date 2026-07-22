import {
  BookingStatus,
  type BookingStatus as BookingStatusType,
  type Category,
} from "@marketplays/shared";
import type { CisFactor } from "@/components/seller/CisBreakdownCard";

export interface SellerBookingActivity {
  id: string;
  listingTitle: string;
  buyerName: string;
  status: BookingStatusType;
  amountPence: number;
  countdown?: string;
  subLabel?: string;
  occurredAt: string;
  /** Inline proof thumbnail after upload (Section 11). */
  proofUrl?: string | null;
}

export interface SellerListingStub {
  id: string;
  title: string;
  category: Category;
  cisScore: number | null;
  status: "draft" | "published" | "paused";
  pricePerDayPence: number;
  imageCount: number;
}

export interface MonthlyRevenuePoint {
  month: string;
  revenuePence: number;
}

/** Seller dashboard mock — revenue-first home (Section 8). */
export const SELLER_KPI = {
  revenue30dPence: 184_250,
  revenueDelta: "+12% vs prior 30d",
  activeBookings: 7,
  avgCisScore: 86,
  occupancyRatePct: 64,
} as const;

/** Derived mock occupancy levels 0–3 for next 30 days (Section 8). */
export const SELLER_OCCUPANCY_30D: readonly number[] = [
  0, 1, 1, 2, 0, 3, 3, 2, 1, 0, 0, 2, 3, 3, 1, 1, 2, 0, 0, 1, 2, 3, 2, 1, 0, 1,
  2, 2, 3, 1,
];

export const SELLER_CIS_BREAKDOWN: readonly CisFactor[] = [
  { label: "Verified foot traffic", value: 88 },
  { label: "On-time proof uploads", value: 76 },
  { label: "Buyer ratings", value: 91 },
  { label: "Listing completeness", value: 64 },
];

export const SELLER_MONTHLY_REVENUE: MonthlyRevenuePoint[] = [
  { month: "Aug", revenuePence: 42_000 },
  { month: "Sep", revenuePence: 51_500 },
  { month: "Oct", revenuePence: 48_200 },
  { month: "Nov", revenuePence: 62_800 },
  { month: "Dec", revenuePence: 71_000 },
  { month: "Jan", revenuePence: 58_400 },
  { month: "Feb", revenuePence: 66_100 },
  { month: "Mar", revenuePence: 74_500 },
  { month: "Apr", revenuePence: 69_200 },
  { month: "May", revenuePence: 81_000 },
  { month: "Jun", revenuePence: 92_400 },
  { month: "Jul", revenuePence: 88_750 },
];

export const SELLER_PENDING_PAYOUT_PENCE = 126_400;

export const SELLER_BOOKING_FEED: SellerBookingActivity[] = [
  {
    id: "bk_1",
    listingTitle: "Pitch-side LED — Riverside FC",
    buyerName: "Northstar Agency",
    status: BookingStatus.Live,
    amountPence: 45_000,
    occurredAt: "2h ago",
  },
  {
    id: "bk_2",
    listingTitle: "Gym entrance board — FitHouse",
    buyerName: "Pulse Nutrition",
    status: BookingStatus.Confirmed,
    amountPence: 18_500,
    occurredAt: "Yesterday",
  },
  {
    id: "bk_3",
    listingTitle: "Café window wrap — Bean & Co",
    buyerName: "Local Bank PLC",
    status: BookingStatus.Pending_Payment,
    amountPence: 9_200,
    countdown: "11h left",
    occurredAt: "3h ago",
  },
  {
    id: "bk_4",
    listingTitle: "Pitch-side LED — Riverside FC",
    buyerName: "City Brewery",
    status: BookingStatus.Awaiting_Buyer_Review,
    amountPence: 32_000,
    subLabel: "Buyer has 48h to rate",
    occurredAt: "1d ago",
  },
  {
    id: "bk_5",
    listingTitle: "School hall banner — Greenvale",
    buyerName: "EduSupply Co",
    status: BookingStatus.Awaiting_Proof,
    amountPence: 12_000,
    occurredAt: "2d ago",
  },
  {
    id: "bk_6",
    listingTitle: "Festival stall fascia — SummerJam",
    buyerName: "Spark Soft Drinks",
    status: BookingStatus.Live,
    amountPence: 27_500,
    occurredAt: "3d ago",
  },
];

export const SELLER_LISTINGS: SellerListingStub[] = [
  {
    id: "lst_1",
    title: "Pitch-side LED — Riverside FC",
    category: "sports_club",
    cisScore: 92,
    status: "published",
    pricePerDayPence: 15_000,
    imageCount: 4,
  },
  {
    id: "lst_2",
    title: "Gym entrance board — FitHouse",
    category: "gym",
    cisScore: 78,
    status: "published",
    pricePerDayPence: 6_500,
    imageCount: 3,
  },
  {
    id: "lst_3",
    title: "Café window wrap — Bean & Co",
    category: "cafe",
    cisScore: null,
    status: "draft",
    pricePerDayPence: 3_200,
    imageCount: 0,
  },
];
