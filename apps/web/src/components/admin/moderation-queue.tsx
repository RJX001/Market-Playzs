"use client";

import { useEffect, useState } from "react";
import {
  approveListing,
  getModerationQueue,
  rejectListing,
} from "@/components/admin/admin-api";
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
 * Approve / Reject removes the row after the API succeeds.
 */
export function ModerationQueue() {
  const [queue, setQueue] = useState<ModerationQueueItem[]>(
    STUB_MODERATION_QUEUE,
  );
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const items = await getModerationQueue();
        if (!cancelled && items) setQueue(items);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Could not load queue.");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function moderate(id: string, action: "approve" | "reject") {
    setBusyId(id);
    setError(null);
    try {
      if (action === "approve") await approveListing(id);
      else await rejectListing(id);
      setQueue((prev) => prev.filter((item) => item.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Moderation failed.");
    } finally {
      setBusyId(null);
    }
  }

  if (queue.length === 0) {
    return (
      <p className="rounded-[14px] border border-[#262C38] bg-[#10141C] px-5 py-6 text-[13px] text-[#9AA3B2]">
        Moderation queue is clear.
      </p>
    );
  }

  return (
    <div className="space-y-3">
      {error ? (
        <p className="text-[13px] text-[#F1544B]" role="alert">
          {error}
        </p>
      ) : null}
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
                disabled={busyId === item.id}
                onClick={() => void moderate(item.id, "approve")}
                className="h-9 rounded-[9px] bg-[#3B5BFF] px-4 text-[13px] font-semibold text-white hover:bg-[#3B5BFF]/90"
              >
                Approve
              </button>
              <button
                type="button"
                disabled={busyId === item.id}
                onClick={() => void moderate(item.id, "reject")}
                className="h-9 rounded-[9px] border border-[#5C1F1F] bg-[#301414] px-4 text-[13px] font-semibold text-[#F1544B] hover:bg-[#301414]/80"
              >
                Reject
              </button>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
