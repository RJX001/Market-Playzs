"use client";

import { useEffect, useState } from "react";
import { KpiCard } from "@/components/admin/kpi-card";
import { ModerationQueue } from "@/components/admin/moderation-queue";
import { OpenDisputesPanel } from "@/components/admin/open-disputes-panel";
import { formatPence } from "@/components/admin/format-money";
import {
  getAdminDisputes,
  getAdminReport,
} from "@/components/admin/admin-api";
import {
  STUB_DISPUTES,
  STUB_HEALTH,
  type AdminDispute,
} from "@/components/admin/stub-data";

type HealthKpis = {
  gmvPence: number;
  activeListings: number;
  pendingModeration: number;
  disputesOpen: number;
  listingsSuspended: number;
};

/** Admin overview — Section 14: KPIs, moderation queue, open disputes. */
export default function AdminOverviewPage() {
  const [health, setHealth] = useState<HealthKpis>({ ...STUB_HEALTH });
  const [disputes, setDisputes] = useState<AdminDispute[]>(STUB_DISPUTES);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [report, disputeItems] = await Promise.all([
          getAdminReport(),
          getAdminDisputes(),
        ]);
        if (cancelled) return;
        if (report) {
          setHealth({
            gmvPence: report.gmvPence,
            activeListings: report.activeListings,
            pendingModeration: report.pendingModeration,
            disputesOpen: report.disputesOpen,
            listingsSuspended: report.listingsSuspended,
          });
        }
        if (disputeItems) setDisputes(disputeItems);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load admin report.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[#F5F6F8]">
          Admin
        </h1>
        <p className="mt-1 text-[13px] text-[#9AA3B2]">
          Platform KPIs, listing moderation, and open disputes.
        </p>
      </div>

      {error ? (
        <p className="text-[13px] text-[#F1544B]" role="alert">
          {error}
        </p>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          value={formatPence(health.gmvPence)}
          label="GMV (30 days)"
        />
        <KpiCard
          value={String(health.activeListings)}
          label="Active listings"
        />
        <KpiCard
          value={String(health.pendingModeration)}
          label="Pending moderation"
          delta="In review queue"
          deltaTone="down"
        />
        <KpiCard
          value={String(health.disputesOpen)}
          label="Open disputes"
          delta="Needs resolution"
          deltaTone="down"
        />
      </div>

      <section className="space-y-3">
        <div>
          <h2 className="text-[15px] font-semibold text-[#F5F6F8]">
            Listing moderation queue
          </h2>
          <p className="mt-0.5 text-[12.5px] text-[#6B7280]">
            Approve or reject new listings. Actions remove the row from this
            stub queue.
          </p>
        </div>
        <ModerationQueue />
      </section>

      <section className="space-y-3">
        <div>
          <h2 className="text-[15px] font-semibold text-[#F5F6F8]">
            Open disputes
          </h2>
          <p className="mt-0.5 text-[12.5px] text-[#6B7280]">
            Full resolution tools live under Disputes.
          </p>
        </div>
        <OpenDisputesPanel disputes={disputes} />
      </section>
    </div>
  );
}
