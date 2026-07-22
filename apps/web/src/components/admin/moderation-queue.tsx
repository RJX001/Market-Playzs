"use client";

import { useState } from "react";
import {
  STUB_MODERATION_QUEUE,
  type ModerationQueueItem,
} from "@/components/admin/stub-data";

const CATEGORY_LABELS: Record<string, string> = {
  sports_club: "Sports club",
  gym: "Gym",
  school: "School",
  shop: "Shop",
  cafe: "Café",
  festival: "Festival",
  community_event: "Community event",
  billboard: "Billboard",
  event_venue: "Event venue",
};

function formatSubmitted(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

/**
 * Section 14 — listing moderation queue.
 * Approve / Reject removes the row locally (stub until API).
 */
export function ModerationQueue() {
  const [queue, setQueue] = useState<ModerationQueueItem[]>(
    STUB_MODERATION_QUEUE,
  );

  function remove(id: string) {
    setQueue((prev) => prev.filter((item) => item.id !== id));
  }

  if (queue.length === 0) {
    return (
      <p className="rounded-[14px] border border-[#262C38] bg-[#10141C] px-5 py-6 text-[13px] text-[#9AA3B2]">
        Moderation queue is clear.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {queue.map((item) => (
        <li
          key={item.id}
          className="flex flex-col gap-4 rounded-[14px] border border-[#262C38] bg-[#10141C] p-5 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="min-w-0">
            <p className="truncate text-[15px] font-semibold text-[#F5F6F8]">
              {item.title}
            </p>
            <p className="mt-1 text-[12.5px] text-[#6B7280]">
              {item.sellerName} ·{" "}
              {CATEGORY_LABELS[item.category] ?? item.category} · Submitted{" "}
              {formatSubmitted(item.submittedAt)}
            </p>
          </div>
          <div className="flex shrink-0 gap-2">
            <button
              type="button"
              onClick={() => remove(item.id)}
              className="h-9 rounded-[9px] bg-[#3B5BFF] px-4 text-[13px] font-semibold text-white hover:bg-[#3B5BFF]/90"
            >
              Approve
            </button>
            <button
              type="button"
              onClick={() => remove(item.id)}
              className="h-9 rounded-[9px] border border-[#5C1F1F] bg-[#301414] px-4 text-[13px] font-semibold text-[#F1544B] hover:bg-[#301414]/80"
            >
              Reject
            </button>
          </div>
        </li>
      ))}
    </ul>
  );
}
