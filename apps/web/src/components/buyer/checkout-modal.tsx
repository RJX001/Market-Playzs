"use client";

import { useEffect, useState } from "react";
import { Check } from "lucide-react";
import { penceToPoundsDisplay } from "@marketplays/shared";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useCampaignCart } from "@/components/buyer/campaign-cart-context";
import { formatWeeklyPriceFromDailyPence } from "@/components/buyer/price";
import { cn } from "@/lib/utils";

export type CheckoutPaymentMethod = "card" | "invoice";

export interface CheckoutModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Called when user confirms — must create bookings via existing booking helpers. */
  onConfirm: (paymentMethod: CheckoutPaymentMethod) => Promise<{
    ok: boolean;
    error?: string;
    bookedCount?: number;
  }>;
  isSubmitting?: boolean;
}

export function CheckoutModal({
  open,
  onOpenChange,
  onConfirm,
  isSubmitting = false,
}: CheckoutModalProps) {
  const { items, totalWeeklyPence, clear } = useCampaignCart();
  const [paymentMethod, setPaymentMethod] =
    useState<CheckoutPaymentMethod>("card");
  const [agreed, setAgreed] = useState(false);
  const [successCount, setSuccessCount] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setAgreed(false);
      setSuccessCount(null);
      setError(null);
      setPaymentMethod("card");
    }
  }, [open]);

  const totalLabel = penceToPoundsDisplay(totalWeeklyPence);
  const canConfirm = agreed && items.length > 0 && !isSubmitting;

  async function handleConfirm(): Promise<void> {
    if (!canConfirm) return;
    setError(null);
    const result = await onConfirm(paymentMethod);
    if (result.ok) {
      setSuccessCount(result.bookedCount ?? items.length);
      clear();
    } else {
      setError(result.error ?? "Booking failed. Try again.");
    }
  }

  function handleDone(): void {
    onOpenChange(false);
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent
        className="w-[480px] max-w-[calc(100%-2rem)] gap-0 rounded-[14px] border border-[#262C38] bg-[#10141C] p-0 text-[#F5F6F8] sm:max-w-[480px]"
        showCloseButton={successCount === null}
      >
        {successCount !== null ? (
          <div className="flex flex-col items-center px-6 py-10 text-center">
            <div className="mb-4 flex size-14 items-center justify-center rounded-full border border-[#155336] bg-[#0C2A1D]">
              <Check className="size-7 text-[#34D399]" strokeWidth={2.5} />
            </div>
            <DialogHeader className="items-center">
              <DialogTitle className="text-[20px] font-bold text-white">
                Booking confirmed
              </DialogTitle>
              <DialogDescription className="text-[14px] text-[#9AA3B2]">
                {successCount} {successCount === 1 ? "space" : "spaces"} booked
                successfully.
              </DialogDescription>
            </DialogHeader>
            <button
              type="button"
              onClick={handleDone}
              className="mt-8 w-full rounded-[9px] bg-[#3B5BFF] px-4 py-2.5 text-[14px] font-semibold text-white"
            >
              Done
            </button>
          </div>
        ) : (
          <div className="flex flex-col">
            <DialogHeader className="border-b border-[#1D2330] px-5 py-4">
              <DialogTitle className="text-[17px] font-bold text-white">
                Checkout
              </DialogTitle>
              <DialogDescription className="text-[13px] text-[#6B7280]">
                Review your campaign cart and confirm booking.
              </DialogDescription>
            </DialogHeader>

            <div className="max-h-[40vh] space-y-0 overflow-y-auto px-5 py-3">
              {items.length === 0 ? (
                <p className="py-6 text-center text-[13px] text-[#6B7280]">
                  Your cart is empty.
                </p>
              ) : (
                items.map(({ listing }) => (
                  <div
                    key={listing.id}
                    className="flex items-start justify-between gap-3 border-b border-[#1D2330] py-3 last:border-0"
                  >
                    <div className="min-w-0">
                      <p className="truncate text-[13px] font-medium text-[#F5F6F8]">
                        {listing.title}
                      </p>
                      <p className="text-[12px] text-[#6B7280]">
                        {listing.city}
                      </p>
                    </div>
                    <p className="shrink-0 text-[13px] font-semibold text-[#F5F6F8]">
                      {formatWeeklyPriceFromDailyPence(
                        listing.pricePerDayPence,
                      )}
                    </p>
                  </div>
                ))
              )}
            </div>

            <div className="flex items-center justify-between border-t border-[#1D2330] px-5 py-3">
              <span className="text-[13px] font-semibold text-[#9AA3B2]">
                Total / week
              </span>
              <span className="text-[16px] font-bold text-white">
                {totalLabel}
              </span>
            </div>

            <div className="space-y-4 px-5 pb-5 pt-2">
              <div>
                <p className="mb-2 text-[12.5px] font-semibold uppercase tracking-[0.04em] text-[#9AA3B2]">
                  Payment method
                </p>
                <div className="inline-flex rounded-[20px] border border-[#262C38] bg-[#10141C] p-0.5">
                  {(
                    [
                      ["card", "Card"],
                      ["invoice", "Invoice net-30"],
                    ] as const
                  ).map(([value, label]) => (
                    <button
                      key={value}
                      type="button"
                      onClick={() => setPaymentMethod(value)}
                      className={cn(
                        "rounded-[18px] px-3.5 py-1.5 text-[12.5px] font-semibold transition-colors",
                        paymentMethod === value
                          ? "bg-[#3B5BFF] text-white"
                          : "text-[#9AA3B2] hover:text-[#F5F6F8]",
                      )}
                    >
                      {label}
                    </button>
                  ))}
                </div>
              </div>

              <label className="flex cursor-pointer items-start gap-2.5 text-[13px] text-[#F5F6F8]">
                <input
                  type="checkbox"
                  checked={agreed}
                  onChange={(e) => setAgreed(e.target.checked)}
                  className="mt-0.5 size-4 accent-[#3B5BFF]"
                />
                <span>I agree to the contract &amp; insurance terms</span>
              </label>

              {error && (
                <p className="rounded-[9px] border border-[#5C1F1F] bg-[#301414] px-3 py-2 text-[12.5px] text-[#F1544B]">
                  {error}
                </p>
              )}

              <button
                type="button"
                disabled={!canConfirm}
                onClick={() => void handleConfirm()}
                className="w-full rounded-[9px] bg-[#3B5BFF] px-4 py-2.5 text-[14px] font-semibold text-white disabled:cursor-not-allowed disabled:opacity-40"
              >
                {isSubmitting
                  ? "Confirming…"
                  : `Confirm & pay ${totalLabel}`}
              </button>
            </div>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
