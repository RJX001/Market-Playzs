import type { AdminDispute } from "@/components/admin/stub-data";

interface OpenDisputesPanelProps {
  disputes: AdminDispute[];
}

/**
 * Section 14 — open disputes rows: booking ref, issue, status badge.
 */
export function OpenDisputesPanel({ disputes }: OpenDisputesPanelProps) {
  const open = disputes.filter((d) => d.status === "open");

  if (open.length === 0) {
    return (
      <p className="rounded-[14px] border border-[#262C38] bg-[#10141C] px-5 py-6 text-[13px] text-[#9AA3B2]">
        No open disputes.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {open.map((dispute) => (
        <li
          key={dispute.id}
          className="flex flex-col gap-3 rounded-[14px] border border-[#262C38] bg-[#10141C] p-5 sm:flex-row sm:items-start sm:justify-between"
        >
          <div className="min-w-0">
            <p className="text-[12.5px] font-medium text-[#6B7280]">
              Booking {dispute.bookingId}
            </p>
            <p className="mt-1 text-[14px] text-[#F5F6F8]">{dispute.reason}</p>
            <p className="mt-1.5 text-[12.5px] text-[#9AA3B2]">
              {dispute.listingTitle} · {dispute.buyerName} ↔ {dispute.sellerName}
              {dispute.firstDecisionDueAt
                ? ` · SLA ${new Date(dispute.firstDecisionDueAt).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" })}`
                : ""}
            </p>
          </div>
          <span className="inline-flex shrink-0 items-center rounded-[20px] border border-[#5C4013] bg-[#2E2409] px-2.5 py-1 text-[11.5px] font-medium text-[#F5A623]">
            Open
          </span>
        </li>
      ))}
    </ul>
  );
}
