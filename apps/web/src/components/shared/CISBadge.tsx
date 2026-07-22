import type { CSSProperties } from "react";
import {
  CIS_DISPLAY_NAME,
  formatCisBadgeLabel,
  getCisBand,
} from "@marketplays/shared";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export interface CISBadgeProps {
  /** Nullable CIS — null renders "CIS New" (grey), never treat as zero. */
  score: number | null;
  className?: string;
}

/**
 * Community Impact Score badge (Section 2.3).
 * ≥85 green · 60–84 amber · <60 red · null grey "CIS New".
 */
export function CISBadge({ score, className }: CISBadgeProps) {
  const band = getCisBand(score);
  const cisStyle = {
    "--cis-color": band.color,
    "--cis-bg": band.background,
    "--cis-border": band.border,
  } as CSSProperties;

  return (
    <Badge
      variant="outline"
      className={cn(
        "rounded-full border-[color:var(--cis-border)] bg-[color:var(--cis-bg)] text-[color:var(--cis-color)]",
        className,
      )}
      style={cisStyle}
      title={`${CIS_DISPLAY_NAME}: ${band.label}${score === null ? "" : ` (${score})`}`}
    >
      {formatCisBadgeLabel(score)}
    </Badge>
  );
}
