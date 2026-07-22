import {
  BOOKING_STATUS_LABELS,
  type BookingStatus,
} from "@marketplays/shared";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

/** Semantic status colours from Section 2.2 — display labels stay sentence-case (Section 15). */
const STATUS_STYLES: Record<BookingStatus, string> = {
  Pending_Payment:
    "border-[var(--status-amber-border)] bg-[var(--status-amber-bg)] text-[var(--status-amber)]",
  Confirmed:
    "border-[var(--status-blue-border)] bg-[var(--status-blue-bg)] text-[var(--status-blue)]",
  Live: "border-[var(--status-green-border)] bg-[var(--status-green-bg)] text-[var(--status-green)]",
  Awaiting_Proof:
    "border-[var(--status-amber-border)] bg-[var(--status-amber-bg)] text-[var(--status-amber)]",
  Awaiting_Buyer_Review:
    "border-[var(--status-amber-border)] bg-[var(--status-amber-bg)] text-[var(--status-amber)]",
  Completed:
    "border-[var(--border)] bg-[var(--muted)] text-[var(--muted-foreground)]",
  Cancelled:
    "border-[var(--border)] bg-[var(--muted)] text-[var(--muted-foreground)]",
  Refunded:
    "border-[var(--border)] bg-[var(--muted)] text-[var(--muted-foreground)]",
  Disputed:
    "border-[var(--status-red-border)] bg-[var(--status-red-bg)] text-[var(--status-red)]",
  Admin_Flagged:
    "border-[var(--status-red-border)] bg-[var(--status-red-bg)] text-[var(--status-red)]",
};

export interface BookingStatusBadgeProps {
  status: BookingStatus;
  /** Optional countdown for Pending_Payment (e.g. "11h left"). */
  countdown?: string;
  /** Optional secondary line (e.g. review window remaining). */
  subLabel?: string;
  className?: string;
}

/**
 * Booking status pill — enum keys unchanged; UI labels sentence-case (Section 15).
 */
export function BookingStatusBadge({
  status,
  countdown,
  subLabel,
  className,
}: BookingStatusBadgeProps) {
  return (
    <div className={cn("inline-flex flex-col items-start gap-0.5", className)}>
      <Badge
        variant="outline"
        className={cn("rounded-full", STATUS_STYLES[status])}
      >
        {BOOKING_STATUS_LABELS[status]}
        {countdown ? (
          <span className="font-normal opacity-80">· {countdown}</span>
        ) : null}
      </Badge>
      {subLabel ? (
        <span className="text-[11.5px] text-[var(--text-tertiary)]">
          {subLabel}
        </span>
      ) : null}
    </div>
  );
}
