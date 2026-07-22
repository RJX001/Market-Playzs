import Link from "next/link";
import { ListingEditor } from "@/components/seller/ListingWizard";

export default function NewListingPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[14px] text-[#6B7280]">
          Create a space buyers can book on the map.
        </p>
        <Link
          href="/listings"
          className="text-[13px] text-[#6B7280] transition-colors hover:text-[#F5F6F8]"
        >
          ← Back to listings
        </Link>
      </div>
      <ListingEditor mode="new" />
    </div>
  );
}
