"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import {
  BOOKING_STATUS_LABELS,
  BookingStatus,
  isBookingStatus,
  penceToPoundsDisplay,
} from "@marketplays/shared";
import { BuyerReviewStars } from "@/components/buyer/buyer-review-stars";
import {
  fetchBuyerCampaigns,
  type BuyerAnalytics,
  type BuyerBooking,
} from "@/components/buyer/campaigns-api";
import { cn } from "@/lib/utils";

type CampaignStatusStyleKey =
  | "Live"
  | "Confirmed"
  | "Completed"
  | "Pending payment";

const STATUS_STYLES: Record<
  CampaignStatusStyleKey,
  { text: string; bg: string; border: string }
> = {
  Live: { text: "#34D399", bg: "#0C2A1D", border: "#155336" },
  Confirmed: { text: "#7AA2FF", bg: "#101B33", border: "#233A6B" },
  Completed: { text: "#9AA3B2", bg: "#171C26", border: "#262C38" },
  "Pending payment": { text: "#F5A623", bg: "#2E2409", border: "#5C4013" },
};

function styleForStatus(status: string): {
  text: string;
  bg: string;
  border: string;
} {
  if (status === BookingStatus.Live || status === "Live") return STATUS_STYLES.Live;
  if (status === BookingStatus.Confirmed || status === "Confirmed") {
    return STATUS_STYLES.Confirmed;
  }
  if (
    status === BookingStatus.Pending_Payment ||
    status === "Pending payment"
  ) {
    return STATUS_STYLES["Pending payment"];
  }
  return STATUS_STYLES.Completed;
}

function formatDay(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
}

function statusLabel(status: string): string {
  if (isBookingStatus(status)) return BOOKING_STATUS_LABELS[status];
  return status;
}

export function CampaignsPageClient() {
  const [data, setData] = useState<BuyerAnalytics | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    const result = await fetchBuyerCampaigns();
    if (!result.ok) {
      setError(result.error);
      setData(null);
    } else {
      setError(null);
      setData(result.data);
    }
    setLoading(false);
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const kpis = data ?? {
    spend30dPence: 0,
    activeCampaigns: 0,
    avgCostPerWeeklyReachPence: 0,
    paymentsDuePence: 0,
    bookings: [] as BuyerBooking[],
  };

  return (
    <div className="mx-auto max-w-[1200px] px-6 py-8">
      <h1 className="text-[26px] font-bold text-white">My campaigns & spend</h1>
      <p className="mt-1 text-[14px] text-[#6B7280]">
        Track everything you&apos;ve booked across sellers, and where budget is
        going.
      </p>

      {error ? (
        <p
          className="mt-4 rounded-[9px] border border-[#5C1F1F] bg-[#301414] px-3 py-2 text-[12.5px] text-[#F1544B]"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          value={penceToPoundsDisplay(kpis.spend30dPence)}
          label="Spend (30 days)"
        />
        <KpiCard
          value={String(kpis.activeCampaigns)}
          label="Active campaigns"
        />
        <KpiCard
          value={penceToPoundsDisplay(kpis.avgCostPerWeeklyReachPence)}
          label="Avg cost per weekly reach"
        />
        <KpiCard
          value={penceToPoundsDisplay(kpis.paymentsDuePence)}
          label="Payments due"
        />
      </div>

      <h2 className="mt-10 text-[16px] font-bold text-white">
        Active campaigns
      </h2>

      {loading ? (
        <p className="mt-4 text-[13px] text-[#6B7280]">Loading bookings…</p>
      ) : kpis.bookings.length === 0 ? (
        <p className="mt-4 text-[13px] text-[#6B7280]">
          No bookings yet.{" "}
          <Link href="/map" className="text-[#3B5BFF] hover:underline">
            Explore map
          </Link>
        </p>
      ) : (
        <ul className="mt-4 space-y-3">
          {kpis.bookings.map((booking) => {
            const style = styleForStatus(booking.status);
            const label = statusLabel(booking.status);
            return (
              <li key={booking.id}>
                <div className="rounded-[14px] border border-[#262C38] bg-[#10141C] px-5 py-[18px]">
                  <Link
                    href={`/campaigns/${booking.id}`}
                    className="flex items-center justify-between gap-4 transition-colors"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[15px] font-semibold text-[#F5F6F8]">
                        {booking.listing_title || booking.listing_id || booking.id}
                      </p>
                      <p className="mt-0.5 text-[12.5px] text-[#6B7280]">
                        {booking.spaces ?? 1}{" "}
                        {(booking.spaces ?? 1) === 1 ? "space" : "spaces"} ·{" "}
                        {formatDay(booking.start_date)} –{" "}
                        {formatDay(booking.end_date)}
                      </p>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <span
                        className="rounded-[20px] border px-2.5 py-0.5 text-[11.5px] font-semibold"
                        style={{
                          color: style.text,
                          backgroundColor: style.bg,
                          borderColor: style.border,
                        }}
                      >
                        {label}
                      </span>
                      <span className="min-w-[4.5rem] text-right text-[15px] font-bold text-[#F5F6F8]">
                        {penceToPoundsDisplay(booking.total_pence)}
                      </span>
                    </div>
                  </Link>
                  {booking.status === BookingStatus.Awaiting_Buyer_Review ? (
                    <div className="mt-3 border-t border-[#1D2330] pt-3">
                      <BuyerReviewStars
                        bookingId={booking.id}
                        onSubmitted={() => void load()}
                      />
                    </div>
                  ) : booking.rating != null ? (
                    <p className="mt-2 text-[12.5px] text-[#9AA3B2]">
                      Your rating: {booking.rating}/5
                    </p>
                  ) : null}
                </div>
              </li>
            );
          })}
        </ul>
      )}

      <p className="mt-6 text-[12px] text-[#6B7280]">
        Bookings from GET /api/bookings, or GET /api/analytics/buyer if the list
        endpoint is not present.{" "}
        <Link href="/map" className="text-[#3B5BFF] hover:underline">
          Explore map
        </Link>
      </p>
    </div>
  );
}

function KpiCard({ value, label }: { value: string; label: string }) {
  return (
    <div className={cn("rounded-[14px] border border-[#262C38] bg-[#10141C] p-5")}>
      <p className="text-[24px] font-bold text-white">{value}</p>
      <p className="mt-1 text-[13px] text-[#9AA3B2]">{label}</p>
    </div>
  );
}
