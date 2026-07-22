interface KpiCardProps {
  value: string;
  label: string;
  delta?: string;
  deltaTone?: "up" | "down" | "neutral";
}

const deltaClass: Record<NonNullable<KpiCardProps["deltaTone"]>, string> = {
  up: "text-[#34D399]",
  down: "text-[#F1544B]",
  neutral: "text-[#9AA3B2]",
};

/** Admin KPI card — Section 14 tokens (#10141C / #262C38). */
export function KpiCard({
  value,
  label,
  delta,
  deltaTone = "neutral",
}: KpiCardProps) {
  return (
    <div className="rounded-[14px] border border-[#262C38] bg-[#10141C] p-[18px]">
      <p className="text-[24px] font-bold tracking-tight text-[#F5F6F8]">
        {value}
      </p>
      <p className="mt-1 text-[13px] text-[#9AA3B2]">{label}</p>
      {delta ? (
        <p className={`mt-2 text-[11.5px] ${deltaClass[deltaTone]}`}>{delta}</p>
      ) : null}
    </div>
  );
}
