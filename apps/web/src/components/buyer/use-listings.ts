"use client";

import { useEffect, useState } from "react";
import { apiFetch, ApiError } from "@/components/buyer/api-client";
import { filterListings } from "@/components/buyer/filter-listings";
import {
  listingsQueryFromFilters,
  mapApiListing,
  type ListingSearchResponse,
} from "@/components/buyer/listing-mapper";
import { MOCK_BUYER_LISTINGS } from "@/components/buyer/mock-listings";
import type { BuyerFilterState, BuyerListing, MapBBox } from "@/components/buyer/types";

const MAX_PAGES = 5;

export interface UseListingsResult {
  listings: BuyerListing[];
  loading: boolean;
  error: string | null;
  usedMock: boolean;
  total: number;
}

async function fetchAllPages(
  query: string,
): Promise<{ items: BuyerListing[]; total: number }> {
  const first = await apiFetch<ListingSearchResponse>(`/api/listings?${query}`);
  const items = (first.items ?? []).map(mapApiListing);
  const total = Number(first.total ?? items.length);
  let page = 2;
  while (items.length < total && page <= MAX_PAGES) {
    const params = new URLSearchParams(query);
    params.set("page", String(page));
    const next = await apiFetch<ListingSearchResponse>(
      `/api/listings?${params.toString()}`,
    );
    const mapped = (next.items ?? []).map(mapApiListing);
    if (mapped.length === 0) break;
    items.push(...mapped);
    page += 1;
  }
  return { items, total };
}

/**
 * GET /api/listings with current filters.
 * On API error only: fall back to mock and surface `error`.
 */
export function useListings(
  filters: BuyerFilterState,
  bbox: MapBBox | null,
): UseListingsResult {
  const [listings, setListings] = useState<BuyerListing[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [usedMock, setUsedMock] = useState(false);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    let cancelled = false;
    const handle = window.setTimeout(() => {
      void (async () => {
        setLoading(true);
        try {
          const query = listingsQueryFromFilters(filters, bbox);
          const { items, total: nextTotal } = await fetchAllPages(query);
          if (cancelled) return;
          setListings(items);
          setTotal(nextTotal);
          setUsedMock(false);
          setError(null);
        } catch (err) {
          if (cancelled) return;
          const message =
            err instanceof ApiError
              ? err.message
              : "Could not load listings from the API.";
          setError(message);
          setUsedMock(true);
          const fallback = filterListings(MOCK_BUYER_LISTINGS, filters);
          setListings(fallback);
          setTotal(fallback.length);
        } finally {
          if (!cancelled) setLoading(false);
        }
      })();
    }, 400);

    return () => {
      cancelled = true;
      window.clearTimeout(handle);
    };
  }, [filters, bbox]);

  return { listings, loading, error, usedMock, total };
}
