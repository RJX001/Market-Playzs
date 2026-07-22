import { DisputeList } from "@/components/admin/dispute-list";
import { STUB_DISPUTES } from "@/components/admin/stub-data";

export default function AdminDisputesPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[#F5F6F8]">
          Disputes
        </h1>
        <p className="mt-1 text-[13px] text-[#9AA3B2]">
          Resolve with exactly three actions: Approve Seller (full payout), Full
          Refund, or Partial Refund (custom %). Each resolution writes an{" "}
          <code className="font-mono text-[#C7CCD6]">audit_logs</code> row.
        </p>
      </div>

      <DisputeList disputes={STUB_DISPUTES} />
    </div>
  );
}
