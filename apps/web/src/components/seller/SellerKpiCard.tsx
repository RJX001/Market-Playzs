import { cn } from "@/lib/utils";
import { sellerCardClass } from "@/components/seller/seller-styles";

export interface SellerKpiCardProps {
  value: string;
  label: string;
  /** Green delta line under the label (revenue only per Section 8). */
  delta?: string;
  className?: string;
}

export function SellerKpiCard({
  value,
  label,
  delta,
  className,
}: SellerKpiCardProps) {
  return (
    <div className={cn(sellerCardClass, "p-5", className)}>
      <p className="text-[24px] font-bold tracking-tight text-[#F5F6F8]">
        {value}
      </p>
      <p className="mt-1 text-[13px] text-[#9AA3B2]">{label}</p>
      {delta ? (
        <p className="mt-1.5 text-[12.5px] font-medium text-[#34D399]">{delta}</p>
      ) : null}
    </div>
  );
}
