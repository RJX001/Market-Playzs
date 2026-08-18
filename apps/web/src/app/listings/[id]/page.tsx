import Link from "next/link";
import { notFound } from "next/navigation";
import { CATEGORY_LABELS, penceToPoundsDisplay } from "@marketplays/shared";
import { CISBadge } from "@/components/shared/CISBadge";
import {
  fetchListingAvailability,
  fetchListingById,
  fetchListingReviews,
} from "@/components/buyer/listing-api";
import { ListingDetailActions } from "@/components/buyer/listing-detail-actions";
import { isoDate } from "@/components/buyer/listing-mapper";
import { formatWeeklyPriceFromDailyPence } from "@/components/buyer/price";
import { buttonVariants } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface ListingDetailPageProps {
  params: Promise<{ id: string }>;
}

export async function generateMetadata({ params }: ListingDetailPageProps) {
  const { id } = await params;
  const { listing } = await fetchListingById(id);
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
  const [{ listing, error, source }, reviewsResult, availabilityResult] =
    await Promise.all([
      fetchListingById(id),
      fetchListingReviews(id),
      fetchListingAvailability(id, isoDate(0), isoDate(19)),
    ]);
  if (!listing) notFound();

  const startDate = isoDate(0);
  const endDate = isoDate(19);
  const reviews = reviewsResult.reviews;
  const days = availabilityResult.days;

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
        {error ? (
          <p className="mb-4 text-sm text-red-600" role="alert">
            {error}
            {source === "mock" ? " Showing mock listing data." : ""}
          </p>
        ) : null}

        {listing.imageUrls[0] ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img
            src={listing.imageUrls[0]}
            alt=""
            className="aspect-[21/9] w-full rounded-xl bg-zinc-100 object-cover"
          />
        ) : (
          <div className="aspect-[21/9] rounded-xl bg-zinc-100" aria-hidden />
        )}

        <div className="mt-6 flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm text-zinc-500">
              {CATEGORY_LABELS[listing.category]} · {listing.city}
            </p>
            <h1 className="mt-1 text-3xl font-semibold tracking-tight">
              {listing.title}
            </h1>
            <p className="mt-2 text-zinc-600">
              {listing.addressLine1}
              {listing.postcode ? `, ${listing.postcode}` : ""}
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

            <h2 className="pt-4 text-lg font-medium">Availability</h2>
            {availabilityResult.error ? (
              <p className="text-sm text-red-600" role="alert">
                {availabilityResult.error}
              </p>
            ) : days.length === 0 ? (
              <p className="text-sm text-zinc-600">
                No availability rows returned for the next 20 days.
              </p>
            ) : (
              <ul className="space-y-1 text-sm text-zinc-700">
                {days.slice(0, 20).map((day) => (
                  <li key={day.day}>
                    {day.day}: {day.is_locked ? "locked" : "available"}
                  </li>
                ))}
              </ul>
            )}

            <h2 className="pt-4 text-lg font-medium">Reviews</h2>
            {reviewsResult.error ? (
              <p className="text-sm text-red-600" role="alert">
                {reviewsResult.error}
              </p>
            ) : reviews.length === 0 ? (
              <p className="text-sm text-zinc-600">No reviews yet.</p>
            ) : (
              <ul className="space-y-3">
                {reviews.map((review, idx) => (
                  <li
                    key={review.id ?? `review-${idx}`}
                    className="rounded-md border border-zinc-200 bg-zinc-50 p-3"
                  >
                    <p className="text-sm font-medium text-zinc-800">
                      {review.rating}/5
                    </p>
                    {review.comment ? (
                      <p className="mt-1 text-sm text-zinc-600">
                        {review.comment}
                      </p>
                    ) : null}
                  </li>
                ))}
              </ul>
            )}
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
            <ListingDetailActions
              listing={listing}
              startDate={startDate}
              endDate={endDate}
            />
          </aside>
        </div>
      </article>
    </div>
  );
}
