import Link from "next/link";
import { notFound } from "next/navigation";
import { CATEGORY_LABELS, penceToPoundsDisplay } from "@marketplays/shared";
import { CISBadge } from "@/components/shared/CISBadge";
import { getMockListingById } from "@/components/buyer/mock-listings";
import { formatWeeklyPriceFromDailyPence } from "@/components/buyer/price";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ListingDetailPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: ListingDetailPageProps) {
  const { id } = await params;
  const listing = getMockListingById(id);
  if (!listing) {
    return { title: "Listing · MarketPlays" };
  }
  return {
    title: `${listing.title} · MarketPlays`,
    description: listing.description.slice(0, 160),
  };
}

/** Public SSR listing detail — light marketing shell (Section 3.1). */
export default async function ListingDetailPage({
  params,
}: ListingDetailPageProps) {
  const { id } = await params;
  const listing = getMockListingById(id);
  if (!listing) notFound();

  return (
    <div className="min-h-screen bg-white text-zinc-900">
      <header className="border-b border-zinc-200 bg-white">
        <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
          <Link href="/" className="text-sm font-semibold tracking-tight">
            <span className="text-zinc-900">Market</span>
            <span className="text-[var(--brand-blue)]">Plays</span>
          </Link>
          <Link
            href="/map"
            className={cn(buttonVariants({ variant: "outline", size: "sm" }))}
          >
            Back to map
          </Link>
        </div>
      </header>

      <article className="mx-auto max-w-5xl px-4 py-10">
        <div className="aspect-[21/9] rounded-xl bg-zinc-100" aria-hidden />

        <div className="mt-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm text-zinc-500">
              {CATEGORY_LABELS[listing.category]} · {listing.city}
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight">
              {listing.title}
            </h1>
            <p className="mt-2 text-zinc-600">
              {listing.addressLine1}, {listing.postcode}
            </p>
          </div>
          <CISBadge score={listing.cisScore} />
        </div>

        <div className="mt-8 grid gap-8 md:grid-cols-[1fr_280px]">
          <div className="space-y-4">
            <h2 className="text-lg font-medium">About this space</h2>
            <p className="leading-relaxed text-zinc-700">
              {listing.description}
            </p>
            <div className="flex flex-wrap gap-2">
              {listing.audienceTags.map((tag) => (
                <span
                  key={tag}
                  className="rounded-md border border-zinc-200 bg-zinc-50 px-2 py-0.5 text-xs text-zinc-600"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>

          <aside className="h-fit rounded-xl border border-zinc-200 bg-zinc-50 p-5">
            <p className="text-2xl font-semibold tracking-tight">
              {formatWeeklyPriceFromDailyPence(listing.pricePerDayPence)}
            </p>
            <p className="mt-1 text-xs text-zinc-500">
              {penceToPoundsDisplay(listing.pricePerDayPence)}/day · shown at
              booking confirmation
            </p>
            <p className="mt-4 text-sm text-zinc-600">
              ~{listing.audienceSize.toLocaleString("en-GB")} weekly reach
            </p>
            <p className="mt-1 text-sm capitalize text-zinc-600">
              {listing.bookingType} booking · {listing.availability}
            </p>
            <Link
              href="/map"
              className={cn(buttonVariants({ size: "lg" }), "mt-6 w-full")}
            >
              {listing.bookingType === "instant"
                ? "Instant book on map"
                : "Request on map"}
            </Link>
          </aside>
        </div>
      </article>
    </div>
  );
}
