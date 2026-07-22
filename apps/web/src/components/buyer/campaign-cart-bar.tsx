"use client";

import { penceToPoundsDisplay } from "@marketplays/shared";
import { useCampaignCart } from "@/components/buyer/campaign-cart-context";
import { cn } from "@/lib/utils";

export interface CampaignCartBarProps {
  onReview: () => void;
  className?: string;
}

export function CampaignCartBar({ onReview, className }: CampaignCartBarProps) {
  const { itemCount, totalWeeklyPence } = useCampaignCart();

  if (itemCount < 1) return null;

  return (
    <div
      className={cn(
        "fixed bottom-6 left-6 z-50 flex items-center gap-4 rounded-[20px] border border-[#262C38] bg-[#10141C] px-4 py-3 text-[#F5F6F8]",
        "shadow-[0_16px_40px_rgba(0,0,0,0.45)]",
        className,
      )}
    >
      <div className="min-w-0">
        <p className="text-[13px] font-semibold">
          {itemCount} {itemCount === 1 ? "space" : "spaces"} in cart
        </p>
        <p className="text-[12px] text-[#9AA3B2]">
          {penceToPoundsDisplay(totalWeeklyPence)}/week
        </p>
      </div>
      <button
        type="button"
        onClick={onReview}
        className="shrink-0 rounded-[9px] bg-[#3B5BFF] px-4 py-2 text-[13px] font-semibold text-white hover:bg-[#3B5BFF]/90"
      >
        Review & book
      </button>
    </div>
  );
}
