"use client";

import { BookingStatus, penceToPoundsDisplay } from "@marketplays/shared";
import { BookingStatusBadge } from "@/components/shared/BookingStatusBadge";
import {
  sellerCardClass,
  sellerOutlineBtnClass,
  sellerPrimaryBtnClass,
} from "@/components/seller/seller-styles";
import { SELLER_BOOKING_FEED } from "@/components/seller/stub-data";

/**
 * Seller bookings (Section 11) — Accept / Decline / Upload proof only.
 * Status labels are sentence-case via BOOKING_STATUS_LABELS; enum unchanged.
 */
export default function SellerBookingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[#F5F6F8]">
          Bookings
        </h1>
        <p className="mt-1 text-[14px] text-[#6B7280]">
          Accept or decline requests, and upload proof of play when due.
        </p>
      </div>

      <ul className="space-y-3">
        {SELLER_BOOKING_FEED.map((booking) => {
          // Request-to-book stubs use Pending_Payment as the actionable seller gate.
          const showAcceptDecline =
            booking.status === BookingStatus.Pending_Payment;
          const showUploadProof =
            booking.status === BookingStatus.Awaiting_Proof;
          const hasProof = Boolean(booking.proofUrl);

          return (
            <li key={booking.id}>
              <div
                className={`${sellerCardClass} flex flex-wrap items-start justify-between gap-4 px-5 py-[18px]`}
              >
                <div className="min-w-0 flex-1 space-y-2">
                  <div className="flex flex-wrap items-start justify-between gap-3">
                    <div className="min-w-0 space-y-1">
                      <p className="text-[15px] font-semibold text-[#F5F6F8]">
                        {booking.listingTitle}
                      </p>
                      <p className="text-[13px] text-[#6B7280]">
                        {booking.buyerName} · {booking.occurredAt}
                      </p>
                    </div>
                    <p className="shrink-0 text-[15px] font-semibold tabular-nums text-[#F5F6F8]">
                      {penceToPoundsDisplay(booking.amountPence)}
                    </p>
                  </div>

                  <BookingStatusBadge
                    status={booking.status}
                    countdown={booking.countdown}
                    subLabel={booking.subLabel}
                  />

                  {hasProof ? (
                    <div
                      className="mt-2 flex h-[72px] w-[108px] items-center justify-center rounded-[9px] border border-[#262C38] bg-[#171C26] text-[11px] text-[#6B7280]"
                      role="img"
                      aria-label="Proof of play uploaded"
                    >
                      Proof uploaded
                    </div>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  {showAcceptDecline ? (
                    <>
                      <button
                        type="button"
                        className={`${sellerPrimaryBtnClass} h-8 px-3 text-xs`}
                        disabled
                      >
                        Accept
                      </button>
                      <button
                        type="button"
                        className={`${sellerOutlineBtnClass} h-8 px-3 text-xs`}
                        disabled
                      >
                        Decline
                      </button>
                    </>
                  ) : null}
                  {showUploadProof && !hasProof ? (
                    <button
                      type="button"
                      className={`${sellerPrimaryBtnClass} h-8 px-3 text-xs`}
                      disabled
                    >
                      Upload proof
                    </button>
                  ) : null}
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
