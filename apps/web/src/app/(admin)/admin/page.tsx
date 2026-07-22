import { KpiCard } from "@/components/admin/kpi-card";
import { ModerationQueue } from "@/components/admin/moderation-queue";
import { OpenDisputesPanel } from "@/components/admin/open-disputes-panel";
import { formatPence } from "@/components/admin/format-money";
import {
  STUB_DISPUTES,
  STUB_HEALTH,
} from "@/components/admin/stub-data";

/** Admin overview — Section 14: KPIs, moderation queue, open disputes. */
export default function AdminOverviewPage() {
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

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          value={formatPence(STUB_HEALTH.gmvPence)}
          label="GMV (30 days)"
        />
        <KpiCard
          value={String(STUB_HEALTH.activeListings)}
          label="Active listings"
        />
        <KpiCard
          value={String(STUB_HEALTH.pendingModeration)}
          label="Pending moderation"
          delta="In review queue"
          deltaTone="down"
        />
        <KpiCard
          value={String(STUB_HEALTH.disputesOpen)}
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
        <OpenDisputesPanel disputes={STUB_DISPUTES} />
      </section>
    </div>
  );
}
