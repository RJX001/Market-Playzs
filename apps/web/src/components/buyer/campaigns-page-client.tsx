"use client";

import Link from "next/link";
import { penceToPoundsDisplay } from "@marketplays/shared";
import { cn } from "@/lib/utils";

/**
 * Mock campaign aggregates until a spend API exists.
 * Structured for later wire-up — replace MOCK_* with fetch results.
 */
const MOCK_KPIS = {
  spend30dPence: 184500,
  activeCampaigns: 3,
  /** Pence per weekly reach unit (illustrative). */
  avgCostPerWeeklyReachPence: 42,
  paymentsDuePence: 62000,
} as const;

type CampaignStatus = "Live" | "Confirmed" | "Completed" | "Pending payment";

interface MockCampaignRow {
  id: string;
  name: string;
  spaces: number;
  dateFrom: string;
  dateTo: string;
  status: CampaignStatus;
  totalPence: number;
}

const MOCK_CAMPAIGNS: MockCampaignRow[] = [
  {
    id: "cmp-shoreditch-june",
    name: "Shoreditch summer push",
    spaces: 3,
    dateFrom: "14 Jun",
    dateTo: "28 Jun",
    status: "Live",
    totalPence: 94500,
  },
  {
    id: "cmp-city-commute",
    name: "City commute screens",
    spaces: 2,
    dateFrom: "1 Jul",
    dateTo: "15 Jul",
    status: "Confirmed",
    totalPence: 62000,
  },
  {
    id: "cmp-hackney-fit",
    name: "Hackney fitness wall",
    spaces: 1,
    dateFrom: "20 May",
    dateTo: "3 Jun",
    status: "Completed",
    totalPence: 25200,
  },
  {
    id: "cmp-cafe-pilot",
    name: "Upper Street café pilot",
    spaces: 1,
    dateFrom: "8 Jul",
    dateTo: "22 Jul",
    status: "Pending payment",
    totalPence: 13300,
  },
];

const STATUS_STYLES: Record<
  CampaignStatus,
  { text: string; bg: string; border: string }
> = {
  Live: { text: "#34D399", bg: "#0C2A1D", border: "#155336" },
  Confirmed: { text: "#7AA2FF", bg: "#101B33", border: "#233A6B" },
  Completed: { text: "#9AA3B2", bg: "#171C26", border: "#262C38" },
  "Pending payment": { text: "#F5A623", bg: "#2E2409", border: "#5C4013" },
};

export function CampaignsPageClient() {
  return (
    <div className="mx-auto max-w-[1200px] px-6 py-8">
      <h1 className="text-[26px] font-bold text-white">My campaigns & spend</h1>
      <p className="mt-1 text-[14px] text-[#6B7280]">
        Track everything you&apos;ve booked across sellers, and where budget is
        going.
      </p>

      <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <KpiCard
          value={penceToPoundsDisplay(MOCK_KPIS.spend30dPence)}
          label="Spend (30 days)"
        />
        <KpiCard
          value={String(MOCK_KPIS.activeCampaigns)}
          label="Active campaigns"
        />
        <KpiCard
          value={penceToPoundsDisplay(MOCK_KPIS.avgCostPerWeeklyReachPence)}
          label="Avg cost per weekly reach"
        />
        <KpiCard
          value={penceToPoundsDisplay(MOCK_KPIS.paymentsDuePence)}
          label="Payments due"
        />
      </div>

      <h2 className="mt-10 text-[16px] font-bold text-white">
        Active campaigns
      </h2>

      <ul className="mt-4 space-y-3">
        {MOCK_CAMPAIGNS.map((campaign) => {
          const style = STATUS_STYLES[campaign.status];
          return (
            <li key={campaign.id}>
              <Link
                href={`/campaigns/${campaign.id}`}
                className="flex items-center justify-between gap-4 rounded-[14px] border border-[#262C38] bg-[#10141C] px-5 py-[18px] transition-colors hover:border-[#3B5BFF]/40"
              >
                <div className="min-w-0">
                  <p className="truncate text-[15px] font-semibold text-[#F5F6F8]">
                    {campaign.name}
                  </p>
                  <p className="mt-0.5 text-[12.5px] text-[#6B7280]">
                    {campaign.spaces}{" "}
                    {campaign.spaces === 1 ? "space" : "spaces"} ·{" "}
                    {campaign.dateFrom} – {campaign.dateTo}
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
                    {campaign.status}
                  </span>
                  <span className="min-w-[4.5rem] text-right text-[15px] font-bold text-[#F5F6F8]">
                    {penceToPoundsDisplay(campaign.totalPence)}
                  </span>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>

      <p className="mt-6 text-[12px] text-[#6B7280]">
        Showing structured mock data until campaign spend endpoints are wired.{" "}
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
