import { sellerCardClass } from "@/components/seller/seller-styles";

export interface CisFactor {
  label: string;
  value: number;
}

interface CisBreakdownCardProps {
  factors: readonly CisFactor[];
}

/** CIS score breakdown — track #1D2330, fill #3B5BFF (Section 8). */
export function CisBreakdownCard({ factors }: CisBreakdownCardProps) {
  return (
    <section className={`${sellerCardClass} flex h-full flex-col p-5`}>
      <h2 className="text-[16px] font-bold text-[#F5F6F8]">
        CIS score breakdown
      </h2>
      <p className="mt-1 text-[13px] text-[#6B7280]">
        Community Impact Score factors across your spaces.
      </p>
      <ul className="mt-5 flex flex-1 flex-col gap-5">
        {factors.map((factor) => {
          const pct = Math.max(0, Math.min(100, factor.value));
          return (
            <li key={factor.label}>
              <div className="mb-1.5 flex items-baseline justify-between gap-2">
                <span className="text-[13px] font-medium text-[#9AA3B2]">
                  {factor.label}
                </span>
                <span className="text-[13px] font-semibold tabular-nums text-[#F5F6F8]">
                  {pct}
                </span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[#1D2330]">
                <div
                  className="h-full rounded-full bg-[#3B5BFF] transition-[width]"
                  style={{ width: `${pct}%` }}
                />
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
