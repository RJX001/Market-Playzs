import { penceToPoundsDisplay } from "@marketplays/shared";
import { sellerCardClass } from "@/components/seller/seller-styles";

interface PendingPayoutCardProps {
  amountPence: number;
}

/**
 * Pending payout — Stripe Connect Separate Charges and Transfers, T+2 settlement.
 */
export function PendingPayoutCard({ amountPence }: PendingPayoutCardProps) {
  return (
    <section className={`${sellerCardClass} p-5`}>
      <h2 className="text-[16px] font-bold text-[#F5F6F8]">Pending payout</h2>
      <p className="mt-3 text-[24px] font-bold tracking-tight text-[#F5F6F8]">
        {penceToPoundsDisplay(amountPence)}
      </p>
      <p className="mt-2 text-[13px] text-[#9AA3B2]">
        Stripe Connect · settles T+2 after campaign completion
      </p>
      <p className="mt-1 text-[12px] text-[#6B7280]">
        Separate Charges and Transfers — funds held until deliverable window
        closes.
      </p>
    </section>
  );
}
