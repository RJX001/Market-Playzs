/** Exact booking status enum from Section 1.3 — do not invent alternate casing. */
export const BookingStatus = {
  Pending_Payment: "Pending_Payment",
  Confirmed: "Confirmed",
  Live: "Live",
  Awaiting_Proof: "Awaiting_Proof",
  Awaiting_Buyer_Review: "Awaiting_Buyer_Review",
  Completed: "Completed",
  Cancelled: "Cancelled",
  Refunded: "Refunded",
  Disputed: "Disputed",
  Admin_Flagged: "Admin_Flagged",
} as const;

export type BookingStatus =
  (typeof BookingStatus)[keyof typeof BookingStatus];

export const BOOKING_STATUS_VALUES: readonly BookingStatus[] = Object.values(
  BookingStatus,
);

export const BOOKING_STATUS_LABELS: Record<BookingStatus, string> = {
  Pending_Payment: "Pending payment",
  Confirmed: "Confirmed",
  Live: "Live",
  Awaiting_Proof: "Awaiting proof",
  Awaiting_Buyer_Review: "Awaiting buyer review",
  Completed: "Completed",
  Cancelled: "Cancelled",
  Refunded: "Refunded",
  Disputed: "Disputed",
  Admin_Flagged: "Admin flagged",
};

export function isBookingStatus(value: string): value is BookingStatus {
  return (BOOKING_STATUS_VALUES as readonly string[]).includes(value);
}
