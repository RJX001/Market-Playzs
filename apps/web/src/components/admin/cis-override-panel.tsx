"use client";

import { useState, useTransition } from "react";
import { AuditNotice } from "@/components/admin/audit-notice";
import { overrideCis } from "@/components/admin/admin-api";
import type { AdminListing } from "@/components/admin/stub-data";

interface CisOverridePanelProps {
  listing: AdminListing;
  onApplied?: (score: number) => void;
}

/**
 * CIS override stub — sets is_cis_overridden visible with asterisk.
 * Audit required (Section 8).
 */
export function CisOverridePanel({ listing, onApplied }: CisOverridePanelProps) {
  const [score, setScore] = useState(
    listing.cisScore ?? 70,
  );
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();
  const [overridden, setOverridden] = useState(listing.isCisOverridden);
  const [displayScore, setDisplayScore] = useState(listing.cisScore);

  function handleOverride() {
    if (score < 0 || score > 100) {
      setMessage("CIS score must be 0–100.");
      return;
    }

    startTransition(async () => {
      setMessage(null);
      // TODO: real /api/admin/listings/{id}/cis-override
      // Server must set is_cis_overridden = true AND write audit_logs
      const result = await overrideCis({
        listingId: listing.id,
        cisScore: score,
      });
      setOverridden(true);
      setDisplayScore(score);
      onApplied?.(score);
      setMessage(
        result.stub
          ? `Stub OK: ${result.path} — is_cis_overridden=true; audit_logs row will be written by API.`
          : "CIS overridden.",
      );
    });
  }

  return (
    <div className="space-y-3 rounded-md border border-zinc-800 bg-zinc-950/80 p-3">
      <p className="text-sm text-zinc-200">
        CIS:{" "}
        <span className="font-semibold tabular-nums">
          {displayScore === null ? "New" : displayScore}
          {overridden ? (
            <abbr
              title="Manual CIS override (is_cis_overridden = true)"
              className="ml-0.5 text-amber-300 no-underline"
            >
              *
            </abbr>
          ) : null}
        </span>
      </p>
      <label className="block text-xs text-zinc-400">
        Override score (0–100)
        <input
          type="number"
          min={0}
          max={100}
          value={score}
          onChange={(e) => setScore(Number(e.target.value))}
          className="mt-1 w-24 rounded-md border border-zinc-700 bg-zinc-950 px-2 py-1.5 text-sm text-zinc-100"
        />
      </label>
      <AuditNotice
        actionLabel={`CIS override on listing ${listing.id} (sets is_cis_overridden)`}
      />
      <button
        type="button"
        disabled={isPending}
        onClick={handleOverride}
        className="rounded-md bg-[#1A56DB] px-3 py-1.5 text-sm font-medium text-white disabled:opacity-50"
      >
        {isPending ? "Saving…" : "Apply CIS override"}
      </button>
      {message ? (
        <p className="text-xs text-emerald-400" role="status">
          {message}
        </p>
      ) : null}
    </div>
  );
}
