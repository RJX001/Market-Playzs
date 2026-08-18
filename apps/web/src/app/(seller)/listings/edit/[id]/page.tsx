"use client";

import { use } from "react";
import Link from "next/link";
import { ListingEditor } from "@/components/seller/ListingWizard";
import { SELLER_LISTINGS } from "@/components/seller/stub-data";

interface EditListingPageProps {
  params: Promise<{ id: string }>;
}

export default function EditListingPage({ params }: EditListingPageProps) {
  const { id } = use(params);
  const listing = SELLER_LISTINGS.find((item) => item.id === id);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[14px] text-[#6B7280]">{listing?.title ?? "Edit listing"}</p>
        <Link
          href="/listings"
          className="text-[13px] text-[#6B7280] transition-colors hover:text-[#F5F6F8]"
        >
          ← Back to listings
        </Link>
      </div>

      <ListingEditor
        mode="edit"
        listingId={id}
        initial={{
          title: listing?.title ?? "",
          category: listing?.category ?? "sports_club",
          description: "",
          pricePerDayPence: listing?.pricePerDayPence ?? 15_000,
          weeklyReach: 2_500,
          address: "",
          bookingType: "instant",
          imageCount: listing?.imageCount ?? 0,
          stripeConnected: listing?.status === "published",
        }}
      />
    </div>
  );
}
