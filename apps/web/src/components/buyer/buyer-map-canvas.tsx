"use client";

import { useMemo, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { resolvePinColour } from "@/components/buyer/pin-colour";
import { formatWeeklyPriceFromDailyPence } from "@/components/buyer/price";
import { BuyerToken } from "@/components/buyer/buyer-tokens";
import type { BuyerListing, MapBBox } from "@/components/buyer/types";
import { useMap } from "@/hooks/useMap";
import { cn } from "@/lib/utils";

interface ProjectedPin {
  listing: BuyerListing;
  xPct: number;
  yPct: number;
  colour: string;
}

/** Rough UK mercator-ish projection for the styled fallback map. */
function projectFallback(
  lat: number,
  lng: number,
  bounds: { west: number; south: number; east: number; north: number },
): { xPct: number; yPct: number } {
  const xPct = ((lng - bounds.west) / (bounds.east - bounds.west)) * 100;
  const yPct = ((bounds.north - lat) / (bounds.north - bounds.south)) * 100;
  return {
    xPct: Math.min(98, Math.max(2, xPct)),
    yPct: Math.min(98, Math.max(2, yPct)),
  };
}

const FALLBACK_BOUNDS = {
  west: -0.2,
  south: 51.45,
  east: 0.05,
  north: 51.58,
};

export interface BuyerMapCanvasProps {
  listings: BuyerListing[];
  selectedId: string | null;
  onPinClick: (listingId: string) => void;
  onViewportChange?: (bbox: MapBBox, zoom: number) => void;
  className?: string;
  /** Hide internal legend when parent renders its own overlays. */
  showLegend?: boolean;
}

export function BuyerMapCanvas({
  listings,
  selectedId,
  onPinClick,
  onViewportChange,
  className,
  showLegend = true,
}: BuyerMapCanvasProps) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [fallbackZoom, setFallbackZoom] = useState(1);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const { mode, ready, error } = useMap({
    containerRef,
    listings,
    selectedId,
    onPinClick,
    onPinDoubleClick: (id) => {
      router.push(`/listings/${id}`);
    },
    onViewportChange,
  });

  const fallbackPins: ProjectedPin[] = useMemo(() => {
    if (mode !== "fallback") return [];
    return listings.map((listing) => {
      const { xPct, yPct } = projectFallback(
        listing.lat,
        listing.lng,
        FALLBACK_BOUNDS,
      );
      return {
        listing,
        xPct,
        yPct,
        colour: resolvePinColour(listing),
      };
    });
  }, [listings, mode]);

  /** Simple grid clusters for fallback — click zooms only. */
  const { singles, clusters } = useMemo(() => {
    if (fallbackZoom >= 2) {
      return { singles: fallbackPins, clusters: [] as ProjectedPin[][] };
    }
    const cell = 8;
    const buckets = new Map<string, ProjectedPin[]>();
    for (const pin of fallbackPins) {
      const key = `${Math.floor(pin.xPct / cell)}_${Math.floor(pin.yPct / cell)}`;
      const list = buckets.get(key) ?? [];
      list.push(pin);
      buckets.set(key, list);
    }
    const nextSingles: ProjectedPin[] = [];
    const nextClusters: ProjectedPin[][] = [];
    for (const group of buckets.values()) {
      if (group.length === 1) nextSingles.push(group[0]!);
      else nextClusters.push(group);
    }
    return { singles: nextSingles, clusters: nextClusters };
  }, [fallbackPins, fallbackZoom]);

  const labelId = hoveredId ?? selectedId;
  const labelPin = singles.find((p) => p.listing.id === labelId);

  return (
    <div
      className={cn(
        "relative h-full min-h-[420px] w-full overflow-hidden",
        className,
      )}
      style={{ backgroundColor: BuyerToken.mapBase }}
    >
      {mode === "mapbox" ? (
        <div ref={containerRef} className="absolute inset-0" />
      ) : (
        <div className="absolute inset-0" style={{ backgroundColor: BuyerToken.mapBase }}>
          {/* Light schematic street grid — §5.3 */}
          <svg
            className="pointer-events-none absolute inset-0 h-full w-full"
            aria-hidden
          >
            <defs>
              <pattern
                id="buyer-schematic-grid"
                width="64"
                height="64"
                patternUnits="userSpaceOnUse"
              >
                <path
                  d="M 64 0 L 0 0 0 64"
                  fill="none"
                  stroke={BuyerToken.mapGrid}
                  strokeWidth="1"
                />
              </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#buyer-schematic-grid)" />
            {/* Block / road shapes */}
            <rect x="8%" y="18%" width="22%" height="14%" rx="2" fill={BuyerToken.mapBlock} opacity="0.9" />
            <rect x="38%" y="12%" width="18%" height="20%" rx="2" fill={BuyerToken.mapBlock} opacity="0.85" />
            <rect x="62%" y="22%" width="26%" height="12%" rx="2" fill={BuyerToken.mapBlock} opacity="0.9" />
            <rect x="12%" y="48%" width="28%" height="16%" rx="2" fill={BuyerToken.mapBlock} opacity="0.8" />
            <rect x="48%" y="52%" width="20%" height="18%" rx="2" fill={BuyerToken.mapBlock} opacity="0.85" />
            <rect x="74%" y="55%" width="16%" height="14%" rx="2" fill={BuyerToken.mapBlock} opacity="0.9" />
            <rect x="5%" y="72%" width="35%" height="10%" rx="2" fill={BuyerToken.mapBlock} opacity="0.75" />
            <rect x="55%" y="78%" width="30%" height="8%" rx="2" fill={BuyerToken.mapBlock} opacity="0.8" />
            {/* Road corridors */}
            <rect x="0" y="42%" width="100%" height="2.2%" fill="#D0D4DC" opacity="0.95" />
            <rect x="32%" y="0" width="1.8%" height="100%" fill="#D0D4DC" opacity="0.95" />
            <rect x="0" y="28%" width="100%" height="1.4%" fill="#D5D8E0" opacity="0.9" />
            <rect x="58%" y="0" width="1.4%" height="100%" fill="#D5D8E0" opacity="0.9" />
          </svg>

          {clusters.map((group) => {
            const avgX =
              group.reduce((s, p) => s + p.xPct, 0) / group.length;
            const avgY =
              group.reduce((s, p) => s + p.yPct, 0) / group.length;
            return (
              <button
                key={`cluster-${avgX}-${avgY}`}
                type="button"
                className="absolute z-10 flex size-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center rounded-full border-2 border-[#9AA3B2] bg-[#10141C] text-xs font-semibold text-white shadow-md"
                style={{ left: `${avgX}%`, top: `${avgY}%` }}
                onClick={() => setFallbackZoom(2)}
                aria-label={`Cluster of ${group.length} listings — zoom in`}
              >
                {group.length}
              </button>
            );
          })}

          {singles.map((pin) => {
            const selected = selectedId === pin.listing.id;
            return (
              <button
                key={pin.listing.id}
                type="button"
                className={cn(
                  "absolute z-20 size-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full shadow-md transition-transform hover:scale-125",
                  selected && "ring-[3px] ring-[#3B5BFF] ring-offset-2 ring-offset-[#E7E9EE]",
                )}
                style={{
                  left: `${pin.xPct}%`,
                  top: `${pin.yPct}%`,
                  backgroundColor: pin.colour,
                }}
                aria-label={pin.listing.title}
                onClick={() => onPinClick(pin.listing.id)}
                onMouseEnter={() => setHoveredId(pin.listing.id)}
                onMouseLeave={() => setHoveredId(null)}
                onDoubleClick={() =>
                  router.push(`/listings/${pin.listing.id}`)
                }
              />
            );
          })}

          {labelPin && (
            <div
              className="pointer-events-none absolute z-30 -translate-x-1/2 -translate-y-[140%] rounded-[20px] bg-[#0A0E16] px-2 py-0.5 text-[11px] font-medium text-white shadow"
              style={{ left: `${labelPin.xPct}%`, top: `${labelPin.yPct}%` }}
            >
              {formatWeeklyPriceFromDailyPence(labelPin.listing.pricePerDayPence)}
            </div>
          )}
        </div>
      )}

      {showLegend && (
        <div className="absolute bottom-3 left-3 z-20 flex items-center gap-3 rounded-[20px] border border-[#262C38] bg-[#10141C]/95 px-3 py-2 text-[11.5px] text-[#F5F6F8] shadow-lg backdrop-blur">
          <LegendDot colour={BuyerToken.pinAvailable} label="Available" />
          <LegendDot colour={BuyerToken.pinLimited} label="Limited" />
          <LegendDot colour={BuyerToken.pinBooked} label="Booked" />
        </div>
      )}

      {!ready && (
        <div className="absolute inset-0 flex items-center justify-center bg-[#E7E9EE]/60 text-sm text-[#6B7280]">
          Loading map…
        </div>
      )}
      {error && (
        <div className="absolute bottom-3 right-3 max-w-xs rounded-md border border-[#5C1F1F] bg-[#301414]/95 px-3 py-2 text-xs text-[#F1544B]">
          {error}
        </div>
      )}
    </div>
  );
}

function LegendDot({ colour, label }: { colour: string; label: string }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span
        className="size-2.5 rounded-full"
        style={{ backgroundColor: colour }}
        aria-hidden
      />
      {label}
    </span>
  );
}
