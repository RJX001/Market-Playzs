"use client";

import { useEffect, useState } from "react";
import { penceToPoundsDisplay } from "@marketplays/shared";
import { BookingActivityFeed } from "@/components/seller/BookingActivityFeed";
import { CisBreakdownCard } from "@/components/seller/CisBreakdownCard";
import { OccupancyHeatmap } from "@/components/seller/OccupancyHeatmap";
import { PendingPayoutCard } from "@/components/seller/PendingPayoutCard";
import { SellerKpiCard } from "@/components/seller/SellerKpiCard";
import {
  getSellerAnalytics,
  getSellerPayouts,
  listSellerBookings,
} from "@/components/seller/seller-api";
import {
  SELLER_BOOKING_FEED,
  SELLER_CIS_BREAKDOWN,
  SELLER_KPI,
  SELLER_OCCUPANCY_30D,
  SELLER_PENDING_PAYOUT_PENCE,
  type SellerBookingActivity,
} from "@/components/seller/stub-data";
import type { CisFactor } from "@/components/seller/CisBreakdownCard";

/**
 * Seller home — Revenue Dashboard (Section 8).
 * KPI row → occupancy heatmap → 1.4fr / 1fr activity + CIS breakdown.
 */
export default function SellerDashboardPage() {
  const [revenue30dPence, setRevenue30dPence] = useState<number>(
    SELLER_KPI.revenue30dPence,
  );
  const [revenueDelta, setRevenueDelta] = useState<string | undefined>(
    SELLER_KPI.revenueDelta,
  );
  const [activeBookings, setActiveBookings] = useState<number>(
    SELLER_KPI.activeBookings,
  );
  const [avgCisScore, setAvgCisScore] = useState<number>(SELLER_KPI.avgCisScore);
  const [occupancyRatePct, setOccupancyRatePct] = useState<number>(
    SELLER_KPI.occupancyRatePct,
  );
  const [occupancy, setOccupancy] = useState<readonly number[]>(
    SELLER_OCCUPANCY_30D,
  );
  const [cisBreakdown, setCisBreakdown] =
    useState<readonly CisFactor[]>(SELLER_CIS_BREAKDOWN);
  const [feed, setFeed] =
    useState<SellerBookingActivity[]>([...SELLER_BOOKING_FEED]);
  const [pendingPayout, setPendingPayout] = useState<number>(
    SELLER_PENDING_PAYOUT_PENCE,
  );
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [analytics, payouts, bookings] = await Promise.all([
          getSellerAnalytics(),
          getSellerPayouts(),
          listSellerBookings(),
        ]);
        if (cancelled) return;
        if (analytics) {
          setRevenue30dPence(analytics.revenue30dPence);
          setRevenueDelta(analytics.revenueDelta);
          setActiveBookings(analytics.activeBookings);
          setAvgCisScore(analytics.avgCisScore);
          setOccupancyRatePct(analytics.occupancyRatePct);
          if (analytics.occupancy30d.length > 0) {
            setOccupancy(analytics.occupancy30d);
          }
          if (analytics.cisBreakdown.length > 0) {
            setCisBreakdown(analytics.cisBreakdown);
          }
          if (analytics.recentBookings.length > 0) {
            setFeed(analytics.recentBookings);
          }
          if (analytics.pendingPayoutPence) {
            setPendingPayout(analytics.pendingPayoutPence);
          }
        }
        if (payouts.pendingPence) {
          setPendingPayout(payouts.pendingPence);
        }
        if (bookings.length > 0) {
          setFeed(bookings);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load dashboard.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[#F5F6F8]">
          Revenue dashboard
        </h1>
        <p className="mt-1 text-[14px] text-[#6B7280]">
          Track earnings, bookings, and Community Impact Score across your
          spaces.
        </p>
      </div>

      {error ? (
        <p className="text-[13px] text-[#F1544B]" role="alert">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SellerKpiCard
          value={penceToPoundsDisplay(revenue30dPence)}
          label="Revenue (30 days)"
          delta={revenueDelta}
        />
        <SellerKpiCard
          value={String(activeBookings)}
          label="Active bookings"
        />
        <SellerKpiCard
          value={String(avgCisScore)}
          label="Avg CIS score"
        />
        <SellerKpiCard
          value={`${occupancyRatePct}%`}
          label="Occupancy rate"
        />
      </div>

      <OccupancyHeatmap levels={occupancy} />

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <BookingActivityFeed items={feed} />
        <div className="space-y-6">
          <CisBreakdownCard factors={cisBreakdown} />
          <PendingPayoutCard amountPence={pendingPayout} />
        </div>
      </div>
    </div>
  );
}
