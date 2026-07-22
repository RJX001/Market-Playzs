"use client";

import { CisOverridePanel } from "@/components/admin/cis-override-panel";
import type { AdminListing } from "@/components/admin/stub-data";

interface ListingsAdminTableProps {
  listings: AdminListing[];
}

/**
 * Admin listings tools.
 * Suspension reason is shown here (admin-only). Seller UI must NOT show it.
 */
export function ListingsAdminTable({ listings }: ListingsAdminTableProps) {
  return (
    <div className="space-y-4">
      <p className="rounded-md border border-zinc-700 bg-zinc-900/50 px-3 py-2 text-xs text-zinc-400">
        Suspended listings are removed from buyer queries immediately. The
        suspension reason is visible to admin tools only — the seller must not
        see the suspension reason in their portal.
      </p>

      <ul className="flex flex-col gap-4">
        {listings.map((listing) => (
          <li
            key={listing.id}
            className="rounded-lg border border-zinc-800 bg-zinc-900/60 p-5"
          >
            <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
              <div>
                <h2 className="text-base font-semibold text-zinc-50">
                  {listing.title}
                  {listing.isCisOverridden ? (
                    <abbr
                      title="is_cis_overridden = true"
                      className="ml-1 text-amber-300 no-underline"
                    >
                      *
                    </abbr>
                  ) : null}
                </h2>
                <p className="text-xs text-zinc-500">
                  {listing.id} · {listing.category} · {listing.sellerName}
                </p>
              </div>
              <span
                className={
                  listing.status === "suspended"
                    ? "text-sm text-red-400"
                    : listing.status === "draft"
                      ? "text-sm text-zinc-400"
                      : "text-sm text-emerald-400"
                }
              >
                {listing.status}
              </span>
            </div>

            {listing.status === "suspended" && listing.suspensionReason ? (
              <div className="mt-3 rounded-md border border-red-500/30 bg-red-500/10 px-3 py-2">
                <p className="text-xs font-medium uppercase tracking-wide text-red-300">
                  Suspension reason (admin only)
                </p>
                <p className="mt-1 text-sm text-red-100">
                  {listing.suspensionReason}
                </p>
                <p className="mt-2 text-xs text-red-200/70">
                  Do not expose this reason in seller-facing UI.
                </p>
              </div>
            ) : null}

            <div className="mt-4">
              <CisOverridePanel listing={listing} />
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
