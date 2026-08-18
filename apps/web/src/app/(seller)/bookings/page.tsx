"use client";

import { useEffect, useRef, useState } from "react";
import { BookingStatus, penceToPoundsDisplay } from "@marketplays/shared";
import { BookingStatusBadge } from "@/components/shared/BookingStatusBadge";
import {
  declineBooking,
  listSellerBookings,
  SellerApiError,
  uploadBookingProof,
  uploadMedia,
} from "@/components/seller/seller-api";
import {
  sellerCardClass,
  sellerOutlineBtnClass,
  sellerPrimaryBtnClass,
} from "@/components/seller/seller-styles";
import {
  SELLER_BOOKING_FEED,
  type SellerBookingActivity,
} from "@/components/seller/stub-data";

/**
 * Seller bookings (Section 11) — Accept / Decline / Upload proof only.
 * Status labels are sentence-case via BOOKING_STATUS_LABELS; enum unchanged.
 */
export default function SellerBookingsPage() {
  const [bookings, setBookings] = useState<SellerBookingActivity[]>(
    SELLER_BOOKING_FEED,
  );
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [proofTargetId, setProofTargetId] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const items = await listSellerBookings();
        if (!cancelled && items.length > 0) setBookings(items);
      } catch (err) {
        if (!cancelled) {
          setError(
            err instanceof Error ? err.message : "Could not load bookings.",
          );
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function refresh() {
    const items = await listSellerBookings();
    if (items.length > 0) setBookings(items);
  }

  async function onDecline(id: string) {
    setBusyId(id);
    setError(null);
    try {
      await declineBooking(id);
      await refresh();
    } catch (err) {
      setError(err instanceof SellerApiError ? err.message : "Decline failed.");
    } finally {
      setBusyId(null);
    }
  }

  async function onProofFile(file: File | undefined) {
    const bookingId = proofTargetId;
    setProofTargetId(null);
    if (!file || !bookingId) return;
    setBusyId(bookingId);
    setError(null);
    try {
      const url = await uploadMedia(file, "proof");
      await uploadBookingProof(bookingId, url);
      setBookings((prev) =>
        prev.map((b) =>
          b.id === bookingId
            ? {
                ...b,
                proofUrl: url,
                status: BookingStatus.Awaiting_Buyer_Review,
              }
            : b,
        ),
      );
      await refresh();
    } catch (err) {
      setError(
        err instanceof SellerApiError ? err.message : "Proof upload failed.",
      );
    } finally {
      setBusyId(null);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

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

      {error ? (
        <p className="text-[13px] text-[#F1544B]" role="alert">
          {error}
        </p>
      ) : null}

      <input
        ref={fileRef}
        type="file"
        accept="image/*,video/*"
        className="hidden"
        onChange={(e) => onProofFile(e.target.files?.[0])}
      />

      <ul className="space-y-3">
        {bookings.map((booking) => {
          // Request-to-book stubs use Pending_Payment as the actionable seller gate.
          const showCancel =
            booking.status === BookingStatus.Pending_Payment ||
            booking.status === BookingStatus.Confirmed;
          const showUploadProof =
            booking.status === BookingStatus.Awaiting_Proof;
          const hasProof = Boolean(booking.proofUrl);
          const busy = busyId === booking.id;

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
                  {showCancel ? (
                    <button
                      type="button"
                      className={`${sellerOutlineBtnClass} h-8 px-3 text-xs`}
                      disabled={busy}
                      onClick={() => onDecline(booking.id)}
                    >
                      Cancel
                    </button>
                  ) : null}
                  {showUploadProof && !hasProof ? (
                    <button
                      type="button"
                      className={`${sellerPrimaryBtnClass} h-8 px-3 text-xs`}
                      disabled={busy}
                      onClick={() => {
                        setProofTargetId(booking.id);
                        fileRef.current?.click();
                      }}
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
