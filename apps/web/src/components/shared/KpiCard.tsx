import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { cn } from "@/lib/utils";

export interface KpiCardProps {
  /** Large leading value (number-first hierarchy — Section 3.3). */
  value: string;
  /** Muted secondary label. */
  label: string;
  /** Optional coloured trend delta. */
  delta?: string;
  deltaTone?: "up" | "down" | "neutral";
  className?: string;
}

const deltaClass: Record<NonNullable<KpiCardProps["deltaTone"]>, string> = {
  up: "text-pin-available",
  down: "text-pin-booked",
  neutral: "text-muted-foreground",
};

/**
 * Shared KPI card for buyer/seller dashboards (Section 3.2).
 * Large value, small muted label, optional coloured trend delta.
 */
export function KpiCard({
  value,
  label,
  delta,
  deltaTone = "neutral",
  className,
}: KpiCardProps) {
  return (
    <Card className={cn(className)}>
      <CardHeader className="pb-0">
        <CardTitle className="text-3xl font-semibold tracking-tight">
          {value}
        </CardTitle>
        <CardDescription>{label}</CardDescription>
      </CardHeader>
      {delta ? (
        <CardContent>
          <p className={cn("text-xs", deltaClass[deltaTone])}>{delta}</p>
        </CardContent>
      ) : null}
    </Card>
  );
}
