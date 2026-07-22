import { ListingsAdminTable } from "@/components/admin/listings-admin-table";
import { STUB_LISTINGS } from "@/components/admin/stub-data";

export default function AdminListingsPage() {
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

      <ListingsAdminTable listings={STUB_LISTINGS} />
    </div>
  );
}
