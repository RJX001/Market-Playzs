"use client";

import { useState, useTransition } from "react";
import { AuditNotice } from "@/components/admin/audit-notice";
import {
  resolveDispute,
  type DisputeResolutionAction,
} from "@/components/admin/admin-api";
import { formatPence } from "@/components/admin/format-money";
import type { AdminDispute } from "@/components/admin/stub-data";

interface DisputeListProps {
  disputes: AdminDispute[];
}

const ACTIONS: {
  id: DisputeResolutionAction;
  label: string;
  description: string;
}[] = [
  {
    id: "approve_seller",
    label: "Approve Seller (full payout)",
    description: "Disputed → Completed with full seller payout.",
  },
  {
    id: "full_refund",
    label: "Full Refund",
    description: "Disputed → Refunded; buyer receives 100% refund.",
  },
  {
    id: "partial_refund",
    label: "Partial Refund (custom %)",
    description: "Disputed → Completed with custom refund percent to buyer.",
  },
];

export function DisputeList({ disputes }: DisputeListProps) {
  const open = disputes.filter((d) => d.status === "open");

  if (open.length === 0) {
    return (
      <p className="text-sm text-zinc-400">No open disputes.</p>
    );
  }

  return (
    <ul className="flex flex-col gap-4">
      {open.map((dispute) => (
        <li key={dispute.id}>
          <DisputeCard dispute={dispute} />
        </li>
      ))}
    </ul>
  );
}

function DisputeCard({ dispute }: { dispute: AdminDispute }) {
  const [action, setAction] = useState<DisputeResolutionAction | null>(null);
  const [refundPercent, setRefundPercent] = useState(50);
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  function handleResolve() {
    if (!action) return;
    if (action === "partial_refund" && (refundPercent < 1 || refundPercent > 99)) {
      setMessage("Partial refund requires a custom % between 1 and 99.");
      return;
    }

    startTransition(async () => {
      setMessage(null);
      // TODO: real /api/admin/disputes/{id}/resolve — server writes audit_logs
      const result = await resolveDispute({
        disputeId: dispute.id,
        action,
        refundPercent: action === "partial_refund" ? refundPercent : undefined,
      });
      setMessage(
        result.stub
          ? `Stub OK: ${result.path} (audit_logs row will be written by API).`
          : "Resolved.",
      );
    });
  }

  return (
    <article className="rounded-[14px] border border-[#262C38] bg-[#10141C] p-5">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-zinc-50">
            {dispute.listingTitle}
          </h2>
          <p className="text-xs text-zinc-500">
            Dispute {dispute.id} · Booking {dispute.bookingId}
          </p>
        </div>
        <p className="text-sm font-medium text-zinc-200">
          {formatPence(dispute.amountPence)}
        </p>
      </div>

      <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
        <div>
          <dt className="text-zinc-500">Buyer</dt>
          <dd className="text-zinc-200">{dispute.buyerName}</dd>
        </div>
        <div>
          <dt className="text-zinc-500">Seller</dt>
          <dd className="text-zinc-200">{dispute.sellerName}</dd>
        </div>
      </dl>

      <p className="mt-3 text-sm text-zinc-300">{dispute.reason}</p>

      <fieldset className="mt-4 space-y-2">
        <legend className="text-sm font-medium text-zinc-200">
          Resolution (exactly three options)
        </legend>
        {ACTIONS.map((item) => (
          <label
            key={item.id}
            className="flex cursor-pointer items-start gap-2 rounded-md border border-zinc-800 px-3 py-2 hover:border-zinc-600"
          >
            <input
              type="radio"
              name={`resolve-${dispute.id}`}
              value={item.id}
              checked={action === item.id}
              onChange={() => setAction(item.id)}
              className="mt-1"
            />
            <span>
              <span className="block text-sm text-zinc-100">{item.label}</span>
              <span className="block text-xs text-zinc-500">{item.description}</span>
            </span>
          </label>
        ))}
      </fieldset>

      {action === "partial_refund" ? (
        <label className="mt-3 block text-sm text-zinc-300">
          Custom refund %
          <input
            type="number"
            min={1}
            max={99}
            value={refundPercent}
            onChange={(e) => setRefundPercent(Number(e.target.value))}
            className="mt-1 w-24 rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-zinc-100"
          />
        </label>
      ) : null}

      {action ? (
        <div className="mt-4 space-y-3">
          <AuditNotice
            actionLabel={
              ACTIONS.find((a) => a.id === action)?.label ?? "dispute resolution"
            }
          />
          <button
            type="button"
            disabled={isPending}
            onClick={handleResolve}
            className="rounded-[9px] bg-[#3B5BFF] px-4 py-2 text-sm font-medium text-white disabled:opacity-50"
          >
            {isPending ? "Submitting…" : "Confirm resolution"}
          </button>
        </div>
      ) : null}

      {message ? (
        <p className="mt-3 text-xs text-emerald-400" role="status">
          {message}
        </p>
      ) : null}
    </article>
  );
}
