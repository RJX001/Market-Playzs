"use client";

import { useCallback, useEffect, useState } from "react";
import type { BuyerFilterState } from "@/components/buyer/types";

const STORAGE_KEY = "marketplays.buyer.savedSearches";

export interface SavedSearch {
  id: string;
  label: string;
  filters: BuyerFilterState;
  createdAt: number;
}

function readStored(): SavedSearch[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as SavedSearch[];
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

function writeStored(searches: SavedSearch[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(searches));
}

function defaultLabel(filters: BuyerFilterState): string {
  const bits: string[] = [];
  if (filters.location.trim()) bits.push(filters.location.trim());
  if (filters.assetTypes.length > 0) {
    bits.push(`${filters.assetTypes.length} types`);
  }
  if (filters.priceMaxWeek !== null) {
    bits.push(`≤£${filters.priceMaxWeek}/wk`);
  }
  bits.push(`${filters.radiusKm} km`);
  return bits.join(" · ") || "Saved search";
}

export function useSavedSearches() {
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setSearches(readStored());
    setHydrated(true);
  }, []);

  const save = useCallback((filters: BuyerFilterState, label?: string) => {
    const entry: SavedSearch = {
      id: `ss-${Date.now()}`,
      label: label?.trim() || defaultLabel(filters),
      filters: { ...filters, assetTypes: [...filters.assetTypes], audience: [...filters.audience] },
      createdAt: Date.now(),
    };
    setSearches((prev) => {
      const next = [entry, ...prev].slice(0, 12);
      writeStored(next);
      return next;
    });
    return entry;
  }, []);

  const remove = useCallback((id: string) => {
    setSearches((prev) => {
      const next = prev.filter((s) => s.id !== id);
      writeStored(next);
      return next;
    });
  }, []);

  return { searches, save, remove, hydrated };
}
