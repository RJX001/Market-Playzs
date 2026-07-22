import { penceToPoundsDisplay } from "@marketplays/shared";
import { BookingStatusBadge } from "@/components/shared/BookingStatusBadge";
import { sellerCardClass } from "@/components/seller/seller-styles";
import type { SellerBookingActivity } from "@/components/seller/stub-data";

interface BookingActivityFeedProps {
  items: SellerBookingActivity[];
}

/** Left column — booking activity (Section 8, 1.4fr). */
export function BookingActivityFeed({ items }: BookingActivityFeedProps) {
  return (
    <section className={`${sellerCardClass} flex h-full min-h-[28rem] flex-col p-5`}>
      <h2 className="text-[16px] font-bold text-[#F5F6F8]">Booking activity</h2>
      <ul className="mt-4 flex-1 space-y-0 overflow-y-auto divide-y divide-[#1D2330]">
        {items.map((item) => (
          <li key={item.id} className="flex items-start justify-between gap-3 py-3.5 first:pt-0">
            <div className="min-w-0 space-y-1.5">
              <p className="truncate text-[14px] font-medium text-[#F5F6F8]">
                {item.listingTitle}
              </p>
              <p className="text-[12.5px] text-[#6B7280]">
                {item.buyerName} · {item.occurredAt}
              </p>
              <BookingStatusBadge
                status={item.status}
                countdown={item.countdown}
                subLabel={item.subLabel}
              />
            </div>
            <p className="shrink-0 text-[14px] font-semibold tabular-nums text-[#F5F6F8]">
              {penceToPoundsDisplay(item.amountPence)}
            </p>
          </li>
        ))}
      </ul>
    </section>
  );
}
