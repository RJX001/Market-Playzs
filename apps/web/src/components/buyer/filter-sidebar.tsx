"use client";

import { CATEGORY_LABELS, type Category } from "@marketplays/shared";
import { X } from "lucide-react";
import type { SavedSearch } from "@/components/buyer/use-saved-searches";
import type { BuyerFilterState } from "@/components/buyer/types";
import { cn } from "@/lib/utils";

const AUDIENCE_OPTIONS = [
  "Commuters",
  "Shoppers",
  "Locals",
  "Families",
  "Fitness",
  "Professionals",
  "Tourists",
  "Culture",
] as const;

const ASSET_OPTIONS = Object.entries(CATEGORY_LABELS) as [Category, string][];

export const DEFAULT_BUYER_FILTERS: BuyerFilterState = {
  location: "London, EC2A",
  radiusKm: 5,
  assetTypes: [],
  audience: [],
  priceMaxWeek: 500,
  availabilityFrom: "2026-06-14",
  availabilityTo: "2026-06-21",
  cisMin: null,
  bookingType: "all",
};

const fieldLabelClass =
  "mb-1.5 block text-[12.5px] font-semibold uppercase tracking-[0.04em] text-[#9AA3B2]";

const inputClass =
  "w-full rounded-[9px] border border-[#262C38] bg-[#171C26] px-3 py-2 text-[14px] text-[#F5F6F8] outline-none placeholder:text-[#6B7280] focus:border-[#3B5BFF]";

const chipClass = (active: boolean) =>
  cn(
    "rounded-[20px] border px-2.5 py-1 text-[12px] font-medium transition-colors",
    active
      ? "border-[#3B5BFF] bg-[#3B5BFF]/20 text-[#F5F6F8]"
      : "border-[#262C38] bg-[#171C26] text-[#9AA3B2] hover:text-[#F5F6F8]",
  );

export interface FilterSidebarProps {
  draft: BuyerFilterState;
  onDraftChange: (next: BuyerFilterState) => void;
  onReset: () => void;
  onSaveSearch: () => void;
  savedSearches?: SavedSearch[];
  onApplySavedSearch?: (search: SavedSearch) => void;
  onRemoveSavedSearch?: (id: string) => void;
  className?: string;
}

export function FilterSidebar({
  draft,
  onDraftChange,
  onReset,
  onSaveSearch,
  savedSearches = [],
  onApplySavedSearch,
  onRemoveSavedSearch,
  className,
}: FilterSidebarProps) {
  function update(partial: Partial<BuyerFilterState>): void {
    onDraftChange({ ...draft, ...partial });
  }

  function toggleAudience(tag: string): void {
    const next = draft.audience.includes(tag)
      ? draft.audience.filter((t) => t !== tag)
      : [...draft.audience, tag];
    update({ audience: next });
  }

  function toggleAsset(category: Category): void {
    const next = draft.assetTypes.includes(category)
      ? draft.assetTypes.filter((c) => c !== category)
      : [...draft.assetTypes, category];
    update({ assetTypes: next });
  }

  const cisSelectValue =
    draft.cisMin === null ? "any" : String(draft.cisMin);

  return (
    <aside
      className={cn(
        "flex h-full w-[320px] shrink-0 flex-col overflow-hidden border-r border-[#1D2330] bg-[#0A0E16]",
        className,
      )}
    >
      <div className="border-b border-[#1D2330] px-4 py-4">
        <h2 className="text-[17px] font-bold text-white">Filters</h2>
        <p className="mt-0.5 text-[13px] text-[#6B7280]">Refine the live map</p>
      </div>

      <div className="flex-1 space-y-5 overflow-y-auto px-4 py-4">
        {/* 1. Location */}
        <div>
          <label htmlFor="filter-location" className={fieldLabelClass}>
            Location
          </label>
          <input
            id="filter-location"
            className={inputClass}
            value={draft.location}
            onChange={(e) => update({ location: e.target.value })}
            placeholder="City or postcode"
          />
        </div>

        {/* 2. Radius 1–10km */}
        <div>
          <div className="mb-1.5 flex items-center justify-between">
            <span className={cn(fieldLabelClass, "mb-0")}>Radius</span>
            <span className="text-[12.5px] text-[#9AA3B2]">
              {draft.radiusKm} km
            </span>
          </div>
          <input
            type="range"
            min={1}
            max={10}
            step={1}
            value={Math.min(10, Math.max(1, draft.radiusKm))}
            onChange={(e) => update({ radiusKm: Number(e.target.value) })}
            className="w-full accent-[#3B5BFF]"
            aria-label="Radius in kilometres"
          />
        </div>

        {/* 3. Asset type — chips */}
        <div>
          <span className={fieldLabelClass}>Asset type</span>
          <div className="flex flex-wrap gap-1.5">
            {ASSET_OPTIONS.map(([value, label]) => {
              const active = draft.assetTypes.includes(value);
              return (
                <button
                  key={value}
                  type="button"
                  onClick={() => toggleAsset(value)}
                  className={chipClass(active)}
                >
                  {label}
                </button>
              );
            })}
          </div>
        </div>

        {/* 4. Audience */}
        <div>
          <span className={fieldLabelClass}>Audience</span>
          <div className="flex flex-wrap gap-1.5">
            {AUDIENCE_OPTIONS.map((tag) => {
              const active = draft.audience.includes(tag);
              return (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleAudience(tag)}
                  className={chipClass(active)}
                >
                  {tag}
                </button>
              );
            })}
          </div>
        </div>

        {/* 5. Price range */}
        <div>
          <label htmlFor="filter-price" className={fieldLabelClass}>
            Price range (£/week max)
          </label>
          <input
            id="filter-price"
            className={inputClass}
            type="number"
            min={0}
            value={draft.priceMaxWeek ?? ""}
            onChange={(e) => {
              const raw = e.target.value;
              update({
                priceMaxWeek: raw === "" ? null : Number(raw),
              });
            }}
            placeholder="Any"
          />
        </div>

        {/* 6. Availability */}
        <div>
          <span className={fieldLabelClass}>Availability</span>
          <div className="grid grid-cols-2 gap-2">
            <input
              type="date"
              className={inputClass}
              value={draft.availabilityFrom}
              onChange={(e) => update({ availabilityFrom: e.target.value })}
              aria-label="Available from"
            />
            <input
              type="date"
              className={inputClass}
              value={draft.availabilityTo}
              onChange={(e) => update({ availabilityTo: e.target.value })}
              aria-label="Available to"
            />
          </div>
        </div>

        {/* 7. Community Impact Score */}
        <div>
          <label htmlFor="filter-cis" className={fieldLabelClass}>
            Community Impact Score
          </label>
          <select
            id="filter-cis"
            className={inputClass}
            value={cisSelectValue}
            onChange={(e) => {
              const v = e.target.value;
              update({ cisMin: v === "any" ? null : Number(v) });
            }}
          >
            <option value="any">Any score</option>
            <option value="85">85+ (excellent)</option>
            <option value="60">60+ (good)</option>
          </select>
        </div>

        {/* 8. Booking type */}
        <div>
          <label htmlFor="filter-booking" className={fieldLabelClass}>
            Booking type
          </label>
          <select
            id="filter-booking"
            className={inputClass}
            value={draft.bookingType}
            onChange={(e) => {
              const v = e.target.value;
              if (v === "all" || v === "instant" || v === "request") {
                update({ bookingType: v });
              }
            }}
          >
            <option value="all">All types</option>
            <option value="instant">Instant book</option>
            <option value="request">Request to book</option>
          </select>
        </div>

        {/* 9. Reset + Save search */}
        <div className="flex gap-2 pt-1">
          <button
            type="button"
            onClick={onReset}
            className="flex-1 rounded-[9px] border border-[#262C38] bg-transparent px-3 py-2.5 text-[13px] font-semibold text-[#F5F6F8] transition-colors hover:bg-[#171C26]"
          >
            Reset
          </button>
          <button
            type="button"
            onClick={onSaveSearch}
            className="flex-1 rounded-[9px] bg-[#3B5BFF] px-3 py-2.5 text-[13px] font-semibold text-white transition-colors hover:bg-[#3B5BFF]/90"
          >
            Save search
          </button>
        </div>

        {/* 10. Saved searches */}
        {savedSearches.length > 0 && (
          <div>
            <span className={fieldLabelClass}>Saved searches</span>
            <ul className="space-y-2">
              {savedSearches.map((search) => (
                <li
                  key={search.id}
                  className="flex items-center gap-2 rounded-[9px] border border-[#1D2330] bg-[#10141C] px-3 py-2"
                >
                  <button
                    type="button"
                    className="min-w-0 flex-1 truncate text-left text-[13px] text-[#F5F6F8] hover:text-[#3B5BFF]"
                    onClick={() => onApplySavedSearch?.(search)}
                  >
                    {search.label}
                  </button>
                  <button
                    type="button"
                    aria-label={`Remove ${search.label}`}
                    className="shrink-0 rounded p-0.5 text-[#6B7280] hover:text-[#F1544B]"
                    onClick={() => onRemoveSavedSearch?.(search.id)}
                  >
                    <X className="size-3.5" />
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </aside>
  );
}
