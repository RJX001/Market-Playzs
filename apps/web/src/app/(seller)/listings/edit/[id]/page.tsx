import Link from "next/link";
import { notFound } from "next/navigation";
import { ListingEditor } from "@/components/seller/ListingWizard";
import { SELLER_LISTINGS } from "@/components/seller/stub-data";

interface EditListingPageProps {
  params: Promise<{ id: string }>;
}

export default async function EditListingPage({ params }: EditListingPageProps) {
  const { id } = await params;
  const listing = SELLER_LISTINGS.find((item) => item.id === id);

  if (!listing) {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-[14px] text-[#6B7280]">{listing.title}</p>
        <Link
          href="/listings"
          className="text-[13px] text-[#6B7280] transition-colors hover:text-[#F5F6F8]"
        >
          ← Back to listings
        </Link>
      </div>

      <ListingEditor
        mode="edit"
        initial={{
          title: listing.title,
          category: listing.category,
          description: "",
          pricePerDayPence: listing.pricePerDayPence,
          weeklyReach: 2_500,
          address: "",
          bookingType: "instant",
          imageCount: listing.imageCount,
          stripeConnected: listing.status === "published",
        }}
      />
    </div>
  );
}
