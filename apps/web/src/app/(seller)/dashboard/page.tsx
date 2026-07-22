import { penceToPoundsDisplay } from "@marketplays/shared";
import { BookingActivityFeed } from "@/components/seller/BookingActivityFeed";
import { CisBreakdownCard } from "@/components/seller/CisBreakdownCard";
import { OccupancyHeatmap } from "@/components/seller/OccupancyHeatmap";
import { SellerKpiCard } from "@/components/seller/SellerKpiCard";
import {
  SELLER_BOOKING_FEED,
  SELLER_CIS_BREAKDOWN,
  SELLER_KPI,
  SELLER_OCCUPANCY_30D,
} from "@/components/seller/stub-data";

/**
 * Seller home — Revenue Dashboard (Section 8).
 * KPI row → occupancy heatmap → 1.4fr / 1fr activity + CIS breakdown.
 */
export default function SellerDashboardPage() {
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

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <SellerKpiCard
          value={penceToPoundsDisplay(SELLER_KPI.revenue30dPence)}
          label="Revenue (30 days)"
          delta={SELLER_KPI.revenueDelta}
        />
        <SellerKpiCard
          value={String(SELLER_KPI.activeBookings)}
          label="Active bookings"
        />
        <SellerKpiCard
          value={String(SELLER_KPI.avgCisScore)}
          label="Avg CIS score"
        />
        <SellerKpiCard
          value={`${SELLER_KPI.occupancyRatePct}%`}
          label="Occupancy rate"
        />
      </div>

      <OccupancyHeatmap levels={SELLER_OCCUPANCY_30D} />

      <div className="grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <BookingActivityFeed items={SELLER_BOOKING_FEED} />
        <CisBreakdownCard factors={SELLER_CIS_BREAKDOWN} />
      </div>
    </div>
  );
}
