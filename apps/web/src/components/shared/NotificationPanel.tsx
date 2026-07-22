"use client";

import { useEffect, useId, useRef, useState } from "react";
import { Bell } from "lucide-react";
import { cn } from "@/lib/utils";

export interface NotificationItem {
  id: string;
  message: string;
  /** Relative time label, e.g. "2h ago" — stub-friendly */
  relativeTime: string;
  unread: boolean;
}

export interface NotificationPanelProps {
  /** Stub/local notifications — no backend schema. */
  items?: NotificationItem[];
  className?: string;
}

const STUB_NOTIFICATIONS: NotificationItem[] = [
  {
    id: "n1",
    message: "Booking confirmed for Riverside Gym — start date Monday.",
    relativeTime: "12m ago",
    unread: true,
  },
  {
    id: "n2",
    message: "Proof of play uploaded for Festival Banner A.",
    relativeTime: "1h ago",
    unread: true,
  },
  {
    id: "n3",
    message: "New message from Northside FC about creative specs.",
    relativeTime: "Yesterday",
    unread: false,
  },
];

/**
 * Bell + unread badge + notifications dropdown (Sections 4 & 13).
 * Opening the panel marks all as read (local UI state only).
 */
export function NotificationPanel({
  items = STUB_NOTIFICATIONS,
  className,
}: NotificationPanelProps) {
  const [open, setOpen] = useState(false);
  const [notifications, setNotifications] = useState(items);
  const panelId = useId();
  const rootRef = useRef<HTMLDivElement>(null);

  const unreadCount = notifications.filter((n) => n.unread).length;

  useEffect(() => {
    if (!open) return;

    function onPointerDown(event: MouseEvent) {
      if (!rootRef.current?.contains(event.target as Node)) {
        setOpen(false);
      }
    }

    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setOpen(false);
    }

    document.addEventListener("mousedown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  function toggleOpen() {
    // Opening marks all read (badge clears) — Section 13 product choice for stub UI.
    if (!open) {
      setNotifications((prev) =>
        prev.map((n) => (n.unread ? { ...n, unread: false } : n)),
      );
    }
    setOpen((wasOpen) => !wasOpen);
  }

  return (
    <div ref={rootRef} className={cn("relative", className)}>
      <button
        type="button"
        aria-label={
          unreadCount > 0
            ? `Notifications, ${unreadCount} unread`
            : "Notifications"
        }
        aria-expanded={open}
        aria-controls={panelId}
        onClick={toggleOpen}
        className="relative flex size-9 items-center justify-center rounded-[9px] border border-[#262C38] bg-[#10141C] text-[#F5F6F8] transition-colors hover:border-[#3B5BFF]/50 hover:text-white"
      >
        <Bell className="size-4" strokeWidth={1.75} aria-hidden="true" />
        {unreadCount > 0 ? (
          <span className="absolute -top-1 -right-1 flex h-[16px] min-w-[16px] items-center justify-center rounded-full bg-[#F1544B] px-1 text-[10px] font-semibold leading-none text-white">
            {unreadCount > 9 ? "9+" : unreadCount}
          </span>
        ) : null}
      </button>

      {open ? (
        <div
          id={panelId}
          role="dialog"
          aria-label="Notifications"
          className="absolute top-[calc(100%+8px)] right-0 z-50 w-[320px] overflow-hidden rounded-[12px] border border-[#262C38] bg-[#10141C] shadow-[var(--shadow-dropdown)] motion-safe:animate-[mp-notif-fade-in_0.18s_ease-out]"
        >
          <div className="border-b border-[#1D2330] px-3.5 py-2.5">
            <p className="text-[13px] text-[#9AA3B2]">Notifications</p>
          </div>
          <ul className="max-h-[320px] overflow-y-auto py-1">
            {notifications.length === 0 ? (
              <li className="px-3.5 py-6 text-center text-[13px] text-[#6B7280]">
                You&apos;re all caught up.
              </li>
            ) : (
              notifications.map((item) => (
                <li
                  key={item.id}
                  className={cn(
                    "border-b border-[#1D2330] px-3.5 py-3 last:border-b-0",
                    item.unread && "bg-[#101B33]",
                  )}
                >
                  <p className="text-[13px] leading-snug text-[#F5F6F8]">
                    {item.message}
                  </p>
                  <p className="mt-1 text-[11.5px] text-[#6B7280]">
                    {item.relativeTime}
                  </p>
                </li>
              ))
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
