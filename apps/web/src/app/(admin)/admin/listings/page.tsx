"use client";

import { useEffect, useState } from "react";
import { ListingsAdminTable } from "@/components/admin/listings-admin-table";
import { getAdminListings } from "@/components/admin/admin-api";
import { STUB_LISTINGS, type AdminListing } from "@/components/admin/stub-data";

export default function AdminListingsPage() {
  const [listings, setListings] = useState<AdminListing[]>(STUB_LISTINGS);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const items = await getAdminListings();
        if (!cancelled && items) setListings(items);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load listings.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[#F5F6F8]">
          Listings
        </h1>
        <p className="mt-1 text-[13px] text-[#9AA3B2]">
          CIS overrides set{" "}
          <code className="font-mono text-[#C7CCD6]">is_cis_overridden</code> and
          show an asterisk. Suspension reasons are admin-only — sellers must not
          see them.
        </p>
      </div>

      {error ? (
        <p className="text-[13px] text-[#F1544B]" role="alert">
          {error}
        </p>
      ) : null}

      <ListingsAdminTable listings={listings} />
    </div>
  );
}
