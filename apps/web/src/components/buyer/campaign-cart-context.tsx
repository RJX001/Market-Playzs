"use client";

import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";
import type { BuyerListing } from "@/components/buyer/types";
import { weeklyPoundsFromDailyPence } from "@/components/buyer/price";

export interface CampaignCartItem {
  listing: BuyerListing;
  addedAt: number;
}

interface CampaignCartContextValue {
  items: CampaignCartItem[];
  itemCount: number;
  /** Total weekly rate in pence (sum of daily × 7). */
  totalWeeklyPence: number;
  totalWeeklyPounds: number;
  isInCart: (listingId: string) => boolean;
  add: (listing: BuyerListing) => void;
  remove: (listingId: string) => void;
  toggle: (listing: BuyerListing) => void;
  clear: () => void;
}

const CampaignCartContext = createContext<CampaignCartContextValue | null>(
  null,
);

export function CampaignCartProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<CampaignCartItem[]>([]);

  const add = useCallback((listing: BuyerListing) => {
    setItems((prev) => {
      if (prev.some((i) => i.listing.id === listing.id)) return prev;
      return [...prev, { listing, addedAt: Date.now() }];
    });
  }, []);

  const remove = useCallback((listingId: string) => {
    setItems((prev) => prev.filter((i) => i.listing.id !== listingId));
  }, []);

  const toggle = useCallback((listing: BuyerListing) => {
    setItems((prev) => {
      if (prev.some((i) => i.listing.id === listing.id)) {
        return prev.filter((i) => i.listing.id !== listing.id);
      }
      return [...prev, { listing, addedAt: Date.now() }];
    });
  }, []);

  const clear = useCallback(() => setItems([]), []);

  const isInCart = useCallback(
    (listingId: string) => items.some((i) => i.listing.id === listingId),
    [items],
  );

  const totalWeeklyPence = useMemo(
    () => items.reduce((sum, i) => sum + i.listing.pricePerDayPence * 7, 0),
    [items],
  );

  const totalWeeklyPounds = useMemo(
    () =>
      items.reduce(
        (sum, i) => sum + weeklyPoundsFromDailyPence(i.listing.pricePerDayPence),
        0,
      ),
    [items],
  );

  const value = useMemo<CampaignCartContextValue>(
    () => ({
      items,
      itemCount: items.length,
      totalWeeklyPence,
      totalWeeklyPounds,
      isInCart,
      add,
      remove,
      toggle,
      clear,
    }),
    [
      items,
      totalWeeklyPence,
      totalWeeklyPounds,
      isInCart,
      add,
      remove,
      toggle,
      clear,
    ],
  );

  return (
    <CampaignCartContext.Provider value={value}>
      {children}
    </CampaignCartContext.Provider>
  );
}

export function useCampaignCart(): CampaignCartContextValue {
  const ctx = useContext(CampaignCartContext);
  if (!ctx) {
    throw new Error("useCampaignCart must be used within CampaignCartProvider");
  }
  return ctx;
}
