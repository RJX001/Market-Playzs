import { cn } from "@/lib/utils";

export interface MarketPlaysLogoProps {
  className?: string;
  /** Show wordmark text beside the mark. Default true. */
  withWordmark?: boolean;
  /**
   * `app` — dark portal chrome (white wordmark, #3B5BFF mark).
   * `marketing` — light landing (uses landing accent via CSS).
   */
  variant?: "app" | "marketing";
}

/**
 * MarketPlays mark + wordmark (Section 4 app shell / Section 3 landing).
 * Mark: 26px rounded square, app primary, white Lora "M".
 */
export function MarketPlaysLogo({
  className,
  withWordmark = true,
  variant = "app",
}: MarketPlaysLogoProps) {
  const isApp = variant === "app";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-2.5",
        isApp ? "text-foreground" : "text-[var(--landing-accent)]",
        className,
      )}
    >
      <span
        aria-hidden="true"
        className={cn(
          "inline-flex size-[26px] shrink-0 items-center justify-center rounded-[7px] text-[14px] font-bold leading-none text-white",
          "font-[family-name:var(--font-lora)]",
          isApp ? "bg-[var(--app-primary)]" : "bg-[var(--landing-accent)]",
        )}
      >
        M
      </span>
      {withWordmark ? (
        <span
          className={cn(
            "font-[family-name:var(--font-lora)] text-[17px] font-bold tracking-tight",
            isApp ? "text-[#F5F6F8]" : "text-[var(--landing-accent)]",
          )}
        >
          MarketPlays
        </span>
      ) : (
        <span className="sr-only">MarketPlays</span>
      )}
    </span>
  );
}
