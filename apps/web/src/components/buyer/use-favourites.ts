"use client";

import { useCallback, useEffect, useState } from "react";
import {
  apiFetch,
  apiFetchOptional,
  ApiError,
} from "@/components/buyer/api-client";

const STORAGE_KEY = "mp_favourite_ids";

function readLocal(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    return Array.isArray(parsed) ? parsed.map(String) : [];
  } catch {
    return [];
  }
}

function writeLocal(ids: string[]): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(ids));
}

function extractIds(payload: unknown): string[] {
  if (!payload) return [];
  if (Array.isArray(payload)) {
    return payload.map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") {
        const rec = item as Record<string, unknown>;
        return String(rec.listing_id ?? rec.listingId ?? rec.id ?? "");
      }
      return "";
    }).filter(Boolean);
  }
  if (typeof payload === "object") {
    const rec = payload as Record<string, unknown>;
    if (Array.isArray(rec.items)) return extractIds(rec.items);
    if (Array.isArray(rec.listing_ids)) return rec.listing_ids.map(String);
    if (Array.isArray(rec.listingIds)) return rec.listingIds.map(String);
  }
  return [];
}

export function useFavourites() {
  const [ids, setIds] = useState<Set<string>>(new Set());
  const [apiAvailable, setApiAvailable] = useState<boolean | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    void (async () => {
      try {
        const result = await apiFetchOptional<unknown>("/api/favourites", {
          auth: true,
        });
        if (cancelled) return;
        if (result.data == null) {
          setApiAvailable(false);
          setIds(new Set(readLocal()));
          return;
        }
        setApiAvailable(true);
        setIds(new Set(extractIds(result.data)));
        setError(null);
      } catch (err) {
        if (cancelled) return;
        setApiAvailable(false);
        setIds(new Set(readLocal()));
        if (err instanceof ApiError && err.status === 401) {
          setError("Log in to sync saved spaces.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const isFavourite = useCallback(
    (listingId: string) => ids.has(listingId),
    [ids],
  );

  const toggle = useCallback(
    async (listingId: string): Promise<void> => {
      setError(null);
      const currently = ids.has(listingId);
      const next = new Set(ids);
      if (currently) next.delete(listingId);
      else next.add(listingId);
      setIds(next);
      writeLocal([...next]);

      if (apiAvailable === false) return;

      try {
        if (currently) {
          await apiFetch(`/api/favourites/${listingId}`, {
            method: "DELETE",
            auth: true,
          });
        } else {
          await apiFetch(`/api/favourites/${listingId}`, {
            method: "POST",
            auth: true,
          });
        }
        setApiAvailable(true);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setApiAvailable(false);
          return;
        }
        const snapshot = new Set(ids);
        setIds(snapshot);
        writeLocal([...snapshot]);
        setError(
          err instanceof ApiError ? err.message : "Could not update favourite.",
        );
      }
    },
    [apiAvailable, ids],
  );

  return { ids, isFavourite, toggle, error, apiAvailable };
}
