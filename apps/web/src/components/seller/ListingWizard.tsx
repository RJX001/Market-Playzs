"use client";

import { useState } from "react";
import { CATEGORY_LABELS, type Category } from "@marketplays/shared";
import { PublishGuard } from "@/components/seller/PublishGuard";
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
  initial?: Partial<ListingEditorValues>;
}

/**
 * Listing editor — modal visual language (Section 10).
 * Used on /listings/new and /listings/edit/[id]; publish guard preserved.
 */
export function ListingEditor({ mode, initial }: ListingEditorProps) {
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
  const imageCount = initial?.imageCount ?? 0;
  const stripeConnected = initial?.stripeConnected ?? false;

  const requiredFieldsComplete =
    title.trim().length > 0 &&
    description.trim().length > 0 &&
    address.trim().length > 0 &&
    pricePerDayPence > 0;

  const canPublish =
    stripeConnected && requiredFieldsComplete && imageCount > 0;

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
          <div className="mt-1.5 grid grid-cols-3 gap-2.5">
            {[0, 1, 2].map((slot) => (
              <button
                key={slot}
                type="button"
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
      </div>

      <div className="flex flex-wrap items-center justify-end gap-2.5 border-t border-[#1D2330] bg-[#0A0E16]/40 px-5 py-4">
        <button type="button" className={sellerOutlineBtnClass}>
          Save as draft
        </button>
        <button
          type="button"
          className={sellerPrimaryBtnClass}
          disabled={!canPublish}
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
