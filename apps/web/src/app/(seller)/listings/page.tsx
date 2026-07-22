import Link from "next/link";
import { CATEGORY_LABELS, penceToPoundsDisplay } from "@marketplays/shared";
import { CISBadge } from "@/components/shared/CISBadge";
import {
  sellerCardClass,
  sellerOutlineBtnClass,
  sellerPrimaryBtnClass,
} from "@/components/seller/seller-styles";
import { SELLER_LISTINGS } from "@/components/seller/stub-data";

const LISTING_STATUS_LABEL: Record<
  (typeof SELLER_LISTINGS)[number]["status"],
  string
> = {
  draft: "Draft",
  published: "Published",
  paused: "Paused",
};

const LISTING_STATUS_STYLE: Record<
  (typeof SELLER_LISTINGS)[number]["status"],
  string
> = {
  published:
    "border-[#155336] bg-[#0C2A1D] text-[#34D399]",
  draft: "border-[#262C38] bg-[#171C26] text-[#9AA3B2]",
  paused: "border-[#5C4013] bg-[#2E2409] text-[#F5A623]",
};

/** My listings — Section 9. */
export default function SellerListingsPage() {
  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[#F5F6F8]">
            My listings
          </h1>
          <p className="mt-1 text-[14px] text-[#6B7280]">
            Manage spaces buyers can discover on the map.
          </p>
        </div>
        <Link href="/listings/new" className={sellerPrimaryBtnClass}>
          New listing
        </Link>
      </div>

      <ul className="space-y-3">
        {SELLER_LISTINGS.map((listing) => (
          <li key={listing.id}>
            <div
              className={`${sellerCardClass} flex flex-wrap items-center justify-between gap-4 px-5 py-[18px]`}
            >
              <div className="min-w-0 space-y-1.5">
                <div className="flex flex-wrap items-center gap-2">
                  <p className="truncate text-[15px] font-semibold text-[#F5F6F8]">
                    {listing.title}
                  </p>
                  <span
                    className={`inline-flex items-center rounded-[20px] border px-2.5 py-0.5 text-[11.5px] font-medium ${LISTING_STATUS_STYLE[listing.status]}`}
                  >
                    {LISTING_STATUS_LABEL[listing.status]}
                  </span>
                  <CISBadge score={listing.cisScore} />
                </div>
                <p className="text-[13px] text-[#6B7280]">
                  {CATEGORY_LABELS[listing.category]} ·{" "}
                  {penceToPoundsDisplay(listing.pricePerDayPence)}/day ·{" "}
                  {listing.imageCount} image
                  {listing.imageCount === 1 ? "" : "s"}
                </p>
              </div>
              <Link
                href={`/listings/edit/${listing.id}`}
                className={`${sellerOutlineBtnClass} h-9 px-3 text-[13px]`}
              >
                Edit
              </Link>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
