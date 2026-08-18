"use client";

import { useEffect, useRef, useState } from "react";
import { CATEGORY_LABELS, type Category } from "@marketplays/shared";
import { PublishGuard } from "@/components/seller/PublishGuard";
import {
  createConnectAccountLink,
  createListing,
  getListing,
  patchListing,
  publishListing,
  SellerApiError,
  uploadMedia,
} from "@/components/seller/seller-api";
import {
  sellerCardClass,
  sellerInputClass,
  sellerLabelClass,
  sellerOutlineBtnClass,
  sellerPrimaryBtnClass,
} from "@/components/seller/seller-styles";

const CATEGORY_OPTIONS = Object.entries(CATEGORY_LABELS) as [
  Category,
  string,
][];

const DEFAULT_LAT = 51.5074;
const DEFAULT_LNG = -0.1278;

export interface ListingEditorValues {
  title: string;
  category: Category;
  description: string;
  pricePerDayPence: number;
  weeklyReach: number;
  address: string;
  bookingType: "instant" | "request";
  imageCount: number;
  stripeConnected: boolean;
}

interface ListingEditorProps {
  mode: "new" | "edit";
  listingId?: string;
  initial?: Partial<ListingEditorValues>;
}

/**
 * Listing editor — modal visual language (Section 10).
 * Used on /listings/new and /listings/edit/[id]; publish guard preserved.
 */
export function ListingEditor({ mode, listingId, initial }: ListingEditorProps) {
  const [id, setId] = useState(listingId ?? "");
  const [title, setTitle] = useState(initial?.title ?? "");
  const [category, setCategory] = useState<Category>(
    initial?.category ?? "sports_club",
  );
  const [description, setDescription] = useState(initial?.description ?? "");
  const [pricePerDayPence, setPricePerDayPence] = useState(
    initial?.pricePerDayPence ?? 15_000,
  );
  const [weeklyReach, setWeeklyReach] = useState(initial?.weeklyReach ?? 2_500);
  const [address, setAddress] = useState(initial?.address ?? "");
  const [bookingType, setBookingType] = useState<"instant" | "request">(
    initial?.bookingType ?? "instant",
  );
  const [images, setImages] = useState<string[]>([]);
  const [stripeConnected, setStripeConnected] = useState(
    initial?.stripeConnected ?? false,
  );
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const imageCount = images.length || initial?.imageCount || 0;

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    if (params.get("stripe") === "return") {
      setStripeConnected(true);
    }
  }, []);

  useEffect(() => {
    if (!listingId) return;
    let cancelled = false;
    (async () => {
      try {
        const listing = await getListing(listingId);
        if (cancelled || !listing) return;
        setId(listing.id);
        setTitle(listing.title);
        setCategory(listing.category);
        setDescription(listing.description ?? "");
        setPricePerDayPence(listing.price_per_day_pence);
        setImages(listing.images ?? []);
        const types = listing.booking_types ?? [];
        if (types.includes("request")) setBookingType("request");
        if (listing.status === "published") setStripeConnected(true);
      } catch {
        /* keep initial */
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [listingId]);

  const requiredFieldsComplete =
    title.trim().length > 0 &&
    description.trim().length > 0 &&
    address.trim().length > 0 &&
    pricePerDayPence > 0;

  const canPublish =
    stripeConnected && requiredFieldsComplete && imageCount > 0;

  function payload() {
    return {
      title: title.trim(),
      description: description.trim(),
      category,
      price_per_day_pence: pricePerDayPence,
      lat: DEFAULT_LAT,
      lng: DEFAULT_LNG,
      images,
      booking_types: [bookingType],
    };
  }

  async function saveDraft() {
    setBusy(true);
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      if (id) {
        const updated = await patchListing(id, payload());
        setId(updated.id);
      } else {
        const created = await createListing(payload());
        setId(created.id);
      }
      setStatusMessage("Draft saved.");
    } catch (err) {
      setErrorMessage(
        err instanceof SellerApiError ? err.message : "Could not save draft.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handlePublish() {
    setBusy(true);
    setErrorMessage(null);
    setStatusMessage(null);
    try {
      let listingIdToPublish = id;
      if (listingIdToPublish) {
        await patchListing(listingIdToPublish, payload());
      } else {
        const created = await createListing(payload());
        listingIdToPublish = created.id;
        setId(created.id);
      }
      const result = await publishListing(listingIdToPublish);
      setStatusMessage(result.message || "Listing published.");
    } catch (err) {
      setErrorMessage(
        err instanceof SellerApiError
          ? err.message
          : "Could not publish listing.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function handleConnectStripe() {
    setBusy(true);
    setErrorMessage(null);
    try {
      const origin = window.location.origin;
      const path = window.location.pathname;
      const result = await createConnectAccountLink({
        refresh_url: `${origin}${path}?stripe=refresh`,
        return_url: `${origin}${path}?stripe=return`,
      });
      window.location.assign(result.url);
    } catch (err) {
      setErrorMessage(
        err instanceof SellerApiError
          ? err.message
          : "Could not start Stripe Connect.",
      );
      setBusy(false);
    }
  }

  async function handlePhotoSelected(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setErrorMessage(null);
    try {
      const url = await uploadMedia(file);
      setImages((prev) => [...prev, url]);
    } catch (err) {
      setErrorMessage(
        err instanceof SellerApiError ? err.message : "Image upload failed.",
      );
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className={`${sellerCardClass} mx-auto w-full max-w-[560px] overflow-hidden`}>
      <div className="border-b border-[#1D2330] px-5 py-4">
        <h2 className="text-[18px] font-bold text-[#F5F6F8]">
          {mode === "new" ? "New listing" : "Edit listing"}
        </h2>
        <p className="mt-0.5 text-[13px] text-[#6B7280]">
          Photos, pricing, and booking type for this space.
        </p>
      </div>

      <div className="space-y-5 px-5 py-5">
        <div>
          <p className={sellerLabelClass}>Photos</p>
          <input
            ref={fileRef}
            type="file"
            accept="image/*"
            className="hidden"
            onChange={(e) => handlePhotoSelected(e.target.files?.[0])}
          />
          <div className="mt-1.5 grid grid-cols-3 gap-2.5">
            {[0, 1, 2].map((slot) => (
              <button
                key={slot}
                type="button"
                disabled={busy}
                onClick={() => {
                  if (slot >= images.length) fileRef.current?.click();
                }}
                className="flex h-[90px] items-center justify-center rounded-[9px] border border-dashed border-[#262C38] bg-[#171C26] text-[12px] text-[#6B7280] transition-colors hover:border-[#3B5BFF]/50 hover:text-[#9AA3B2]"
              >
                {slot < imageCount ? `Photo ${slot + 1}` : "Add photo"}
              </button>
            ))}
          </div>
        </div>

        <label className="block">
          <span className={sellerLabelClass}>Title</span>
          <input
            className={sellerInputClass}
            placeholder="e.g. Pitch-side LED board"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>

        <label className="block">
          <span className={sellerLabelClass}>Category</span>
          <select
            className={sellerInputClass}
            value={category}
            onChange={(e) => setCategory(e.target.value as Category)}
          >
            {CATEGORY_OPTIONS.map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </label>

        <label className="block">
          <span className={sellerLabelClass}>Description</span>
          <textarea
            className={`${sellerInputClass} min-h-[88px] resize-y`}
            placeholder="What buyers need to know about this space"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block">
            <span className={sellerLabelClass}>Price / day (pence)</span>
            <input
              type="number"
              className={sellerInputClass}
              value={pricePerDayPence}
              onChange={(e) => setPricePerDayPence(Number(e.target.value))}
            />
          </label>
          <label className="block">
            <span className={sellerLabelClass}>Weekly reach</span>
            <input
              type="number"
              className={sellerInputClass}
              value={weeklyReach}
              onChange={(e) => setWeeklyReach(Number(e.target.value))}
            />
          </label>
        </div>

        <label className="block">
          <span className={sellerLabelClass}>Address</span>
          <input
            className={sellerInputClass}
            placeholder="Venue address"
            value={address}
            onChange={(e) => setAddress(e.target.value)}
          />
        </label>

        <div>
          <p className={sellerLabelClass}>Booking type</p>
          <div className="mt-1.5 inline-flex rounded-[20px] border border-[#262C38] bg-[#10141C] p-1">
            {(
              [
                ["instant", "Instant book"],
                ["request", "Request to book"],
              ] as const
            ).map(([value, label]) => {
              const active = bookingType === value;
              return (
                <button
                  key={value}
                  type="button"
                  onClick={() => setBookingType(value)}
                  className={`rounded-[16px] px-3.5 py-1.5 text-[13px] font-semibold transition-colors ${
                    active
                      ? "bg-[#3B5BFF] text-white"
                      : "text-[#9AA3B2] hover:text-[#F5F6F8]"
                  }`}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        <PublishGuard
          stripeConnected={stripeConnected}
          requiredFieldsComplete={requiredFieldsComplete}
          imageCount={imageCount}
        />

        {errorMessage ? (
          <p className="text-[13px] text-[#F1544B]" role="alert">
            {errorMessage}
          </p>
        ) : null}
        {statusMessage ? (
          <p className="text-[13px] text-[#34D399]" role="status">
            {statusMessage}
          </p>
        ) : null}
      </div>

      <div className="flex flex-wrap items-center justify-end gap-2.5 border-t border-[#1D2330] bg-[#0A0E16]/40 px-5 py-4">
        {!stripeConnected ? (
          <button
            type="button"
            className={sellerOutlineBtnClass}
            disabled={busy}
            onClick={handleConnectStripe}
          >
            Connect Stripe
          </button>
        ) : null}
        <button
          type="button"
          className={sellerOutlineBtnClass}
          disabled={busy}
          onClick={saveDraft}
        >
          Save as draft
        </button>
        <button
          type="button"
          className={sellerPrimaryBtnClass}
          disabled={!canPublish || busy}
          onClick={handlePublish}
          title={
            canPublish
              ? undefined
              : "Complete publish checklist before publishing"
          }
        >
          Publish listing
        </button>
      </div>
    </div>
  );
}

/** @deprecated Prefer ListingEditor — kept as alias for existing imports. */
export function ListingWizard() {
  return <ListingEditor mode="new" />;
}
