"use client";

import { useCallback, useEffect, useState } from "react";
import {
  apiFetch,
  apiFetchOptional,
  ApiError,
} from "@/components/buyer/api-client";
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

function normalizeSearch(raw: unknown): SavedSearch | null {
  if (!raw || typeof raw !== "object") return null;
  const rec = raw as Record<string, unknown>;
  const filters = (rec.filters ?? rec.filter ?? rec.query) as
    | BuyerFilterState
    | undefined;
  if (!filters || typeof filters !== "object") {
    return {
      id: String(rec.id ?? `ss-${Date.now()}`),
      label: String(rec.label ?? rec.name ?? "Saved search"),
      filters: rec as unknown as BuyerFilterState,
      createdAt: Number(rec.created_at ?? rec.createdAt ?? Date.now()),
    };
  }
  return {
    id: String(rec.id ?? `ss-${Date.now()}`),
    label: String(rec.label ?? rec.name ?? defaultLabel(filters)),
    filters: {
      ...filters,
      assetTypes: [...(filters.assetTypes ?? [])],
      audience: [...(filters.audience ?? [])],
    },
    createdAt: Number(rec.created_at ?? rec.createdAt ?? Date.now()),
  };
}

function extractSearches(payload: unknown): SavedSearch[] {
  const list = Array.isArray(payload)
    ? payload
    : payload && typeof payload === "object" && "items" in payload
      ? (payload as { items: unknown[] }).items
      : [];
  return list
    .map(normalizeSearch)
    .filter((item): item is SavedSearch => item !== null);
}

export function useSavedSearches() {
  const [searches, setSearches] = useState<SavedSearch[]>([]);
  const [hydrated, setHydrated] = useState(false);
  const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const result = await apiFetchOptional<unknown>("/api/saved-searches", {
          auth: true,
        });
        if (cancelled) return;
        if (result.data == null) {
          setApiAvailable(false);
          setSearches(readStored());
        } else {
          setApiAvailable(true);
          const fromApi = extractSearches(result.data);
          setSearches(fromApi);
          writeStored(fromApi);
        }
      } catch (err) {
        if (cancelled) return;
        setApiAvailable(false);
        setSearches(readStored());
        void err;
      } finally {
        if (!cancelled) setHydrated(true);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const save = useCallback(
    (filters: BuyerFilterState, label?: string) => {
      const entry: SavedSearch = {
        id: `ss-${Date.now()}`,
        label: label?.trim() || defaultLabel(filters),
        filters: {
          ...filters,
          assetTypes: [...filters.assetTypes],
          audience: [...filters.audience],
        },
        createdAt: Date.now(),
      };
      setSearches((prev) => {
        const next = [entry, ...prev].slice(0, 12);
        writeStored(next);
        return next;
      });
      if (apiAvailable !== false) {
        void (async () => {
          try {
            const created = await apiFetch<unknown>("/api/saved-searches", {
              method: "POST",
              auth: true,
              body: JSON.stringify({
                label: entry.label,
                filters: entry.filters,
              }),
            });
            setApiAvailable(true);
            const mapped = normalizeSearch(created);
            if (mapped) {
              setSearches((prev) => {
                const withoutLocal = prev.filter((s) => s.id !== entry.id);
                const next = [mapped, ...withoutLocal].slice(0, 12);
                writeStored(next);
                return next;
              });
            }
          } catch (err) {
            if (err instanceof ApiError && err.status === 404) {
              setApiAvailable(false);
            }
          }
        })();
      }
      return entry;
    },
    [apiAvailable],
  );

  const remove = useCallback(
    (id: string) => {
      setSearches((prev) => {
        const next = prev.filter((s) => s.id !== id);
        writeStored(next);
        return next;
      });
      if (apiAvailable !== false) {
        void (async () => {
          try {
            await apiFetch(`/api/saved-searches/${id}`, {
              method: "DELETE",
              auth: true,
            });
            setApiAvailable(true);
          } catch (err) {
            if (err instanceof ApiError && err.status === 404) {
              setApiAvailable(false);
            }
          }
        })();
      }
    },
    [apiAvailable],
  );

  return { searches, save, remove, hydrated };
}
