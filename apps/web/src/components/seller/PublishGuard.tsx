import {
  sellerCardClass,
} from "@/components/seller/seller-styles";

/**
 * Publish guard stub (Section 10).
 * Blocks publish if: no Stripe Connect, missing required fields, or zero images.
 * Inline red validation per field — not a single generic banner.
 */
export interface PublishGuardProps {
  stripeConnected: boolean;
  requiredFieldsComplete: boolean;
  imageCount: number;
}

export function PublishGuard({
  stripeConnected,
  requiredFieldsComplete,
  imageCount,
}: PublishGuardProps) {
  return (
    <div
      className={`${sellerCardClass} space-y-2 border-[#262C38] bg-[#0A0E16]/60 p-4`}
    >
      <p className="text-[13px] font-semibold text-[#F5F6F8]">
        Publish checklist
      </p>

      <p
        className={`text-[13px] ${
          stripeConnected ? "text-[#34D399]" : "text-[#F1544B]"
        }`}
      >
        {stripeConnected
          ? "Stripe Connect account linked"
          : "Stripe Connect account required — connect payouts before publishing"}
      </p>

      <p
        className={`text-[13px] ${
          requiredFieldsComplete ? "text-[#34D399]" : "text-[#F1544B]"
        }`}
      >
        {requiredFieldsComplete
          ? "Required listing fields complete"
          : "Required fields incomplete — title, description, address, and price"}
      </p>

      <p
        className={`text-[13px] ${
          imageCount > 0 ? "text-[#34D399]" : "text-[#F1544B]"
        }`}
      >
        {imageCount > 0
          ? `${imageCount} image${imageCount === 1 ? "" : "s"} attached`
          : "At least one image is required"}
      </p>
    </div>
  );
}
