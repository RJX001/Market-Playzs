"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
  type RefObject,
} from "react";
import type { BuyerListing, MapBBox } from "@/components/buyer/types";
import { resolvePinColour } from "@/components/buyer/pin-colour";

export interface UseMapOptions {
  containerRef: RefObject<HTMLDivElement | null>;
  listings: BuyerListing[];
  selectedId: string | null;
  onPinClick: (listingId: string) => void;
  onPinDoubleClick: (listingId: string) => void;
  onViewportChange?: (bbox: MapBBox, zoom: number) => void;
  /** London-ish default centre. */
  initialCenter?: [number, number];
  initialZoom?: number;
}

export interface UseMapResult {
  mode: "mapbox" | "fallback";
  ready: boolean;
  error: string | null;
}

const LONDON: [number, number] = [-0.09, 51.52];

function getToken(): string | undefined {
  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN;
  return token && token.length > 0 ? token : undefined;
}

function bboxFromBounds(bounds: {
  getWest: () => number;
  getSouth: () => number;
  getEast: () => number;
  getNorth: () => number;
}): MapBBox {
  return {
    west: bounds.getWest(),
    south: bounds.getSouth(),
    east: bounds.getEast(),
    north: bounds.getNorth(),
  };
}

/**
 * Mapbox GL when NEXT_PUBLIC_MAPBOX_TOKEN is set; otherwise a no-op hook —
 * the fallback canvas is rendered by BuyerMapCanvas.
 *
 * Re-query rules (Section 6): pan >25% viewport or zoom ≥2 levels, debounce 400ms.
 * Cluster click zooms only; single unclustered pin opens slide-in.
 */
export function useMap({
  containerRef,
  listings,
  selectedId,
  onPinClick,
  onPinDoubleClick,
  onViewportChange,
  initialCenter = LONDON,
  initialZoom = 11,
}: UseMapOptions): UseMapResult {
  const token = getToken();
  const mode: "mapbox" | "fallback" = token ? "mapbox" : "fallback";
  const [ready, setReady] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mapRef = useRef<import("mapbox-gl").Map | null>(null);
  const lastQueryRef = useRef<{
    center: [number, number];
    zoom: number;
    width: number;
    height: number;
  } | null>(null);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const clickTimers = useRef<Map<string, ReturnType<typeof setTimeout>>>(
    new Map(),
  );

  const onPinClickRef = useRef(onPinClick);
  const onPinDoubleClickRef = useRef(onPinDoubleClick);
  const onViewportChangeRef = useRef(onViewportChange);
  onPinClickRef.current = onPinClick;
  onPinDoubleClickRef.current = onPinDoubleClick;
  onViewportChangeRef.current = onViewportChange;

  const maybeEmitViewport = useCallback(() => {
    const map = mapRef.current;
    if (!map || !onViewportChangeRef.current) return;

    const center = map.getCenter();
    const zoom = map.getZoom();
    const canvas = map.getCanvas();
    const width = canvas.clientWidth;
    const height = canvas.clientHeight;
    const prev = lastQueryRef.current;

    const bounds = map.getBounds();
    if (!bounds) return;

    let shouldQuery = !prev;
    if (prev) {
      const zoomDelta = Math.abs(zoom - prev.zoom);
      const dx = Math.abs(center.lng - prev.center[0]);
      const dy = Math.abs(center.lat - prev.center[1]);
      const lngSpan = Math.abs(bounds.getEast() - bounds.getWest()) || 1;
      const latSpan = Math.abs(bounds.getNorth() - bounds.getSouth()) || 1;
      const panFrac = Math.max(dx / lngSpan, dy / latSpan);
      shouldQuery = zoomDelta >= 2 || panFrac > 0.25;
    }

    if (!shouldQuery) return;

    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      const m = mapRef.current;
      if (!m || !onViewportChangeRef.current) return;
      const nextBounds = m.getBounds();
      if (!nextBounds) return;
      const c = m.getCenter();
      lastQueryRef.current = {
        center: [c.lng, c.lat],
        zoom: m.getZoom(),
        width,
        height,
      };
      onViewportChangeRef.current(bboxFromBounds(nextBounds), m.getZoom());
    }, 400);
  }, []);

  useEffect(() => {
    if (mode !== "mapbox" || !token) {
      setReady(true);
      return;
    }

    const container = containerRef.current;
    if (!container) return;

    let cancelled = false;
    let map: import("mapbox-gl").Map | null = null;

    async function init(): Promise<void> {
      try {
        const mapboxgl = (await import("mapbox-gl")).default;
        await import("mapbox-gl/dist/mapbox-gl.css");
        if (cancelled || !containerRef.current) return;

        mapboxgl.accessToken = token!;
        map = new mapboxgl.Map({
          container: containerRef.current,
          style: "mapbox://styles/mapbox/light-v11",
          center: initialCenter,
          zoom: initialZoom,
        });
        mapRef.current = map;

        map.addControl(new mapboxgl.NavigationControl({ showCompass: false }), "top-right");

        map.on("load", () => {
          if (!map || cancelled) return;

          map.addSource("listings", {
            type: "geojson",
            data: { type: "FeatureCollection", features: [] },
            cluster: true,
            clusterMaxZoom: 14,
            clusterRadius: 50,
          });

          map.addLayer({
            id: "clusters",
            type: "circle",
            source: "listings",
            filter: ["has", "point_count"],
            paint: {
              "circle-color": "#10141C",
              "circle-radius": [
                "step",
                ["get", "point_count"],
                16,
                5,
                20,
                10,
                24,
              ],
              "circle-stroke-width": 2,
              "circle-stroke-color": "#9AA3B2",
            },
          });

          map.addLayer({
            id: "cluster-count",
            type: "symbol",
            source: "listings",
            filter: ["has", "point_count"],
            layout: {
              "text-field": ["get", "point_count_abbreviated"],
              "text-size": 12,
            },
            paint: {
              "text-color": "#F5F6F8",
            },
          });

          map.addLayer({
            id: "unclustered-point",
            type: "circle",
            source: "listings",
            filter: ["!", ["has", "point_count"]],
            paint: {
              "circle-color": ["get", "colour"],
              "circle-radius": 8,
              "circle-stroke-width": [
                "case",
                ["==", ["get", "selected"], 1],
                3,
                2,
              ],
              "circle-stroke-color": [
                "case",
                ["==", ["get", "selected"], 1],
                "#3B5BFF",
                "#E7E9EE",
              ],
            },
          });

          map.on("click", "clusters", (e) => {
            if (!map) return;
            const features = map.queryRenderedFeatures(e.point, {
              layers: ["clusters"],
            });
            const feature = features[0];
            if (!feature || feature.geometry.type !== "Point") return;
            const clusterId = feature.properties?.cluster_id as
              | number
              | undefined;
            const source = map.getSource(
              "listings",
            ) as import("mapbox-gl").GeoJSONSource;
            if (clusterId === undefined) return;
            source.getClusterExpansionZoom(clusterId, (err, zoom) => {
              if (err || zoom === null || zoom === undefined || !map) return;
              if (feature.geometry.type !== "Point") return;
              const coords = feature.geometry.coordinates as [number, number];
              map.easeTo({ center: coords, zoom });
            });
          });

          map.on("click", "unclustered-point", (e) => {
            const feature = e.features?.[0];
            const id = feature?.properties?.id as string | undefined;
            if (!id) return;
            const existing = clickTimers.current.get(id);
            if (existing) {
              clearTimeout(existing);
              clickTimers.current.delete(id);
              onPinDoubleClickRef.current(id);
              return;
            }
            const timer = setTimeout(() => {
              clickTimers.current.delete(id);
              onPinClickRef.current(id);
            }, 250);
            clickTimers.current.set(id, timer);
          });

          map.on("mouseenter", "clusters", () => {
            map!.getCanvas().style.cursor = "pointer";
          });
          map.on("mouseleave", "clusters", () => {
            map!.getCanvas().style.cursor = "";
          });
          map.on("mouseenter", "unclustered-point", () => {
            map!.getCanvas().style.cursor = "pointer";
          });
          map.on("mouseleave", "unclustered-point", () => {
            map!.getCanvas().style.cursor = "";
          });

          map.on("moveend", maybeEmitViewport);
          setReady(true);
          maybeEmitViewport();
        });
      } catch (err) {
        const message =
          err instanceof Error ? err.message : "Failed to initialise Mapbox";
        setError(message);
        setReady(true);
      }
    }

    void init();

    return () => {
      cancelled = true;
      if (debounceRef.current) clearTimeout(debounceRef.current);
      const timers = clickTimers.current;
      timers.forEach((t) => clearTimeout(t));
      timers.clear();
      map?.remove();
      mapRef.current = null;
    };
  }, [mode, token, containerRef, initialCenter, initialZoom, maybeEmitViewport]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || mode !== "mapbox" || !ready) return;
    const source = map.getSource("listings") as
      | import("mapbox-gl").GeoJSONSource
      | undefined;
    if (!source) return;

    const features = listings.map((listing) => ({
      type: "Feature" as const,
      properties: {
        id: listing.id,
        colour: resolvePinColour(listing),
        selected: selectedId === listing.id ? 1 : 0,
      },
      geometry: {
        type: "Point" as const,
        coordinates: [listing.lng, listing.lat] as [number, number],
      },
    }));

    source.setData({
      type: "FeatureCollection",
      features,
    });
  }, [listings, selectedId, mode, ready]);

  return { mode, ready, error };
}
