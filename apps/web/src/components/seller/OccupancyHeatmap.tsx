import { sellerCardClass } from "@/components/seller/seller-styles";

/** 4-level green intensity: empty → fully booked (Section 8). */
const LEVEL_COLORS = ["#171C26", "#123D26", "#186B36", "#22C55E"] as const;

export interface OccupancyHeatmapProps {
  /** 30 intensity levels 0–3; derived/mock occupancy is fine when no API. */
  levels: readonly number[];
}

export function OccupancyHeatmap({ levels }: OccupancyHeatmapProps) {
  const cells = Array.from({ length: 30 }, (_, i) => levels[i] ?? 0);

  return (
    <section className={`${sellerCardClass} p-5`}>
      <h2 className="text-[16px] font-bold text-[#F5F6F8]">
        Occupancy — next 30 days
      </h2>
      <div
        className="mt-4 grid gap-1.5"
        style={{ gridTemplateColumns: "repeat(30, minmax(0, 1fr))" }}
      >
        {cells.map((level, index) => {
          const clamped = Math.max(0, Math.min(3, Math.round(level)));
          return (
            <div
              key={index}
              title={`Day ${index + 1}: level ${clamped}`}
              className="aspect-square min-h-[10px] rounded-[3px]"
              style={{ backgroundColor: LEVEL_COLORS[clamped] }}
            />
          );
        })}
      </div>
      <div className="mt-3 flex items-center gap-3 text-[11.5px] text-[#6B7280]">
        <span>Empty</span>
        <div className="flex gap-1">
          {LEVEL_COLORS.map((color) => (
            <span
              key={color}
              className="size-2.5 rounded-[2px]"
              style={{ backgroundColor: color }}
            />
          ))}
        </div>
        <span>Fully booked</span>
      </div>
    </section>
  );
}
