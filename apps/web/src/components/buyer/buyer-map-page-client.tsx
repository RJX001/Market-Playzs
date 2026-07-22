"use client";

import { useCallback, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { SlidersHorizontal } from "lucide-react";
import { BuyerMapCanvas } from "@/components/buyer/buyer-map-canvas";
import { CampaignCartBar } from "@/components/buyer/campaign-cart-bar";
import {
  CampaignCartProvider,
  useCampaignCart,
} from "@/components/buyer/campaign-cart-context";
import {
  CheckoutModal,
  type CheckoutPaymentMethod,
} from "@/components/buyer/checkout-modal";
import {
  DEFAULT_BUYER_FILTERS,
  FilterSidebar,
} from "@/components/buyer/filter-sidebar";
import { filterListings } from "@/components/buyer/filter-listings";
import { ListingSlideInPanel } from "@/components/buyer/listing-slide-in-panel";
import { ListingsGrid } from "@/components/buyer/listings-grid";
import { MOCK_BUYER_LISTINGS } from "@/components/buyer/mock-listings";
import { useSavedSearches } from "@/components/buyer/use-saved-searches";
import type { BuyerFilterState, BuyerListing } from "@/components/buyer/types";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet";
import { useBooking } from "@/hooks/useBooking";
import { cn } from "@/lib/utils";

type ViewMode = "map" | "grid";

function BuyerMapPageInner() {
  const router = useRouter();
  const [filters, setFilters] =
    useState<BuyerFilterState>(DEFAULT_BUYER_FILTERS);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [panelOpen, setPanelOpen] = useState(false);
  const [mobileFiltersOpen, setMobileFiltersOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>("map");
  const [checkoutOpen, setCheckoutOpen] = useState(false);

  const { startBooking, startCampaignBookings, isSubmitting } = useBooking();
  const { isInCart, toggle, items } = useCampaignCart();
  const { searches, save, remove } = useSavedSearches();

  const listings = useMemo(
    () => filterListings(MOCK_BUYER_LISTINGS, filters),
    [filters],
  );

  const selectedListing: BuyerListing | null = useMemo(() => {
    if (!selectedId) return null;
    return (
      listings.find((l) => l.id === selectedId) ??
      MOCK_BUYER_LISTINGS.find((l) => l.id === selectedId) ??
      null
    );
  }, [listings, selectedId]);

  const handlePinClick = useCallback((id: string) => {
    setSelectedId(id);
    setPanelOpen(true);
  }, []);

  const handleOpenChange = useCallback((open: boolean) => {
    setPanelOpen(open);
    if (!open) setSelectedId(null);
  }, []);

  const resetFilters = useCallback(() => {
    setFilters(DEFAULT_BUYER_FILTERS);
    setMobileFiltersOpen(false);
  }, []);

  const handleSaveSearch = useCallback(() => {
    save(filters);
  }, [filters, save]);

  const handleCheckoutConfirm = useCallback(
    async (paymentMethod: CheckoutPaymentMethod) => {
      const result = await startCampaignBookings(
        items.map((i) => i.listing),
        filters.availabilityFrom,
        filters.availabilityTo,
        paymentMethod,
      );
      if (!result.ok) {
        return { ok: false, error: result.error, bookedCount: result.bookedCount };
      }
      return { ok: true, bookedCount: result.bookedCount };
    },
    [
      items,
      filters.availabilityFrom,
      filters.availabilityTo,
      startCampaignBookings,
    ],
  );

  return (
    <div className="flex h-[calc(100vh-3.5rem)] min-h-0 w-full bg-[#05070C]">
      <FilterSidebar
        className="hidden md:flex"
        draft={filters}
        onDraftChange={setFilters}
        onReset={resetFilters}
        onSaveSearch={handleSaveSearch}
        savedSearches={searches}
        onApplySavedSearch={(s) =>
          setFilters({
            ...s.filters,
            radiusKm: Math.min(10, Math.max(1, s.filters.radiusKm)),
          })
        }
        onRemoveSavedSearch={remove}
      />

      <div
        className={cn(
          "relative min-w-0 flex-1 transition-[margin] duration-200",
          panelOpen ? "md:mr-[360px]" : "md:mr-0",
        )}
      >
        {viewMode === "map" ? (
          <BuyerMapCanvas
            listings={listings}
            selectedId={selectedId}
            onPinClick={handlePinClick}
          />
        ) : (
          <ListingsGrid
            listings={listings}
            selectedId={selectedId}
            onSelect={handlePinClick}
          />
        )}

        {/* Top-left: count pill + Map/Grid toggle */}
        <div className="absolute left-[18px] top-[18px] z-30 flex flex-wrap items-center gap-2">
          <button
            type="button"
            className="inline-flex items-center gap-1.5 rounded-[20px] border border-[#262C38] bg-[#10141C] px-3 py-1.5 text-[12.5px] font-medium text-white shadow md:hidden"
            onClick={() => setMobileFiltersOpen(true)}
          >
            <SlidersHorizontal className="size-3.5" />
            Filters
          </button>
          <div className="rounded-[20px] bg-[#10141C] px-3 py-1.5 text-[12.5px] font-medium text-white shadow">
            {listings.length} spaces in view
          </div>
          <div className="inline-flex rounded-[20px] border border-[#262C38] bg-[#10141C] p-0.5 shadow">
            {(
              [
                ["map", "Map"],
                ["grid", "Grid"],
              ] as const
            ).map(([mode, label]) => (
              <button
                key={mode}
                type="button"
                onClick={() => setViewMode(mode)}
                className={cn(
                  "rounded-[18px] px-3 py-1 text-[12.5px] font-semibold transition-colors",
                  viewMode === mode
                    ? "bg-[#3B5BFF] text-white"
                    : "text-[#9AA3B2] hover:text-white",
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <Sheet open={mobileFiltersOpen} onOpenChange={setMobileFiltersOpen}>
        <SheetContent
          side="left"
          className="w-[320px] border-[#1D2330] bg-[#0A0E16] p-0 sm:max-w-[320px]"
        >
          <SheetHeader className="sr-only">
            <SheetTitle>Filters</SheetTitle>
          </SheetHeader>
          <FilterSidebar
            className="w-full max-w-none border-0"
            draft={filters}
            onDraftChange={setFilters}
            onReset={resetFilters}
            onSaveSearch={() => {
              handleSaveSearch();
              setMobileFiltersOpen(false);
            }}
            savedSearches={searches}
            onApplySavedSearch={(s) => {
              setFilters(s.filters);
              setMobileFiltersOpen(false);
            }}
            onRemoveSavedSearch={remove}
          />
        </SheetContent>
      </Sheet>

      <ListingSlideInPanel
        listing={selectedListing}
        open={panelOpen}
        onOpenChange={handleOpenChange}
        inCart={selectedListing ? isInCart(selectedListing.id) : false}
        onToggleCart={(listing) => toggle(listing)}
        onBook={(listing) => {
          void startBooking(
            listing,
            filters.availabilityFrom,
            filters.availabilityTo,
          );
        }}
        onMessageSeller={(listing) => {
          router.push(`/messages?listing=${listing.id}`);
        }}
      />

      <CampaignCartBar
        className="md:left-[calc(320px+1.5rem)]"
        onReview={() => setCheckoutOpen(true)}
      />

      <CheckoutModal
        open={checkoutOpen}
        onOpenChange={setCheckoutOpen}
        onConfirm={handleCheckoutConfirm}
        isSubmitting={isSubmitting}
      />
    </div>
  );
}

export function BuyerMapPageClient() {
  return (
    <CampaignCartProvider>
      <BuyerMapPageInner />
    </CampaignCartProvider>
  );
}
