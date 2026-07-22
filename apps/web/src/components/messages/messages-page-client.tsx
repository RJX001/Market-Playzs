"use client";

import { useState } from "react";
import { cn } from "@/lib/utils";
import {
  STUB_THREADS,
  type Message,
  type MessageThread,
} from "@/components/messages/stub-data";

function formatThreadTime(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleString("en-GB", {
    day: "numeric",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Section 12 — two-column messages: thread list + conversation.
 * Stub local state; swap STUB_THREADS for API later.
 */
export function MessagesPageClient() {
  const [threads, setThreads] = useState<MessageThread[]>(STUB_THREADS);
  const [activeId, setActiveId] = useState(STUB_THREADS[0]?.id ?? "");
  const [draft, setDraft] = useState("");

  const active = threads.find((t) => t.id === activeId) ?? null;

  function selectThread(id: string) {
    setActiveId(id);
    setThreads((prev) =>
      prev.map((t) => (t.id === id ? { ...t, unread: false } : t)),
    );
  }

  function sendMessage() {
    const body = draft.trim();
    if (!body || !active) return;

    const next: Message = {
      id: `msg_local_${Date.now()}`,
      fromSelf: true,
      body,
      sentAt: new Date().toISOString(),
    };

    setThreads((prev) =>
      prev.map((t) =>
        t.id === active.id
          ? {
              ...t,
              lastPreview: body,
              updatedAt: next.sentAt,
              messages: [...t.messages, next],
            }
          : t,
      ),
    );
    setDraft("");
  }

  return (
    <div className="mx-auto flex h-[calc(100vh-3.5rem)] max-w-[1200px] flex-col px-4 py-4">
      <div className="mb-4 shrink-0">
        <h1 className="text-[26px] font-bold tracking-tight text-[#F5F6F8]">
          Messages
        </h1>
        <p className="mt-1 text-[13px] text-[#9AA3B2]">
          Buyer ↔ seller threads for active bookings.
        </p>
      </div>

      <div className="grid min-h-0 flex-1 overflow-hidden rounded-[14px] border border-[#262C38] bg-[#10141C] lg:grid-cols-[320px_1fr]">
        {/* Thread list */}
        <aside className="flex min-h-0 flex-col border-b border-[#1D2330] lg:border-r lg:border-b-0">
          <div className="shrink-0 border-b border-[#1D2330] px-4 py-3">
            <p className="text-[13px] font-medium text-[#9AA3B2]">Inbox</p>
          </div>
          <ul className="min-h-0 flex-1 overflow-y-auto" role="list">
            {threads.map((thread) => {
              const selected = thread.id === activeId;
              return (
                <li key={thread.id}>
                  <button
                    type="button"
                    onClick={() => selectThread(thread.id)}
                    className={cn(
                      "w-full border-b border-[#1D2330] px-4 py-3.5 text-left transition-colors",
                      selected
                        ? "bg-[#101B33]"
                        : "hover:bg-[#171C26]/80",
                    )}
                    aria-current={selected ? "true" : undefined}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <p
                        className={cn(
                          "truncate text-[14px] font-semibold",
                          thread.unread ? "text-[#F5F6F8]" : "text-[#F5F6F8]",
                        )}
                      >
                        {thread.counterpartName}
                      </p>
                      {thread.unread ? (
                        <span
                          className="mt-1 size-2 shrink-0 rounded-full bg-[#3B5BFF]"
                          aria-label="Unread"
                        />
                      ) : null}
                    </div>
                    <p className="mt-0.5 truncate text-[12.5px] text-[#6B7280]">
                      {thread.listingTitle}
                    </p>
                    <p className="mt-1.5 line-clamp-1 text-[13px] text-[#9AA3B2]">
                      {thread.lastPreview}
                    </p>
                  </button>
                </li>
              );
            })}
          </ul>
        </aside>

        {/* Conversation */}
        <section className="flex min-h-0 flex-col">
          {active ? (
            <>
              <header className="shrink-0 border-b border-[#1D2330] px-5 py-3.5">
                <p className="text-[15px] font-semibold text-[#F5F6F8]">
                  {active.counterpartName}
                </p>
                <p className="mt-0.5 text-[12.5px] text-[#6B7280]">
                  {active.listingTitle}
                </p>
              </header>

              <div className="min-h-0 flex-1 space-y-3 overflow-y-auto px-5 py-4">
                {active.messages.map((msg) => (
                  <div
                    key={msg.id}
                    className={cn(
                      "flex",
                      msg.fromSelf ? "justify-end" : "justify-start",
                    )}
                  >
                    <div
                      className={cn(
                        "max-w-[70%] rounded-[12px] px-[14px] py-[10px] text-[13.5px] leading-relaxed",
                        msg.fromSelf
                          ? "bg-[#3B5BFF] text-white"
                          : "bg-[#171C26] text-[#C7CCD6]",
                      )}
                    >
                      <p>{msg.body}</p>
                      <p
                        className={cn(
                          "mt-1.5 text-[11.5px]",
                          msg.fromSelf ? "text-white/70" : "text-[#6B7280]",
                        )}
                      >
                        {formatThreadTime(msg.sentAt)}
                      </p>
                    </div>
                  </div>
                ))}
              </div>

              <form
                className="flex shrink-0 gap-2 border-t border-[#1D2330] p-4"
                onSubmit={(e) => {
                  e.preventDefault();
                  sendMessage();
                }}
              >
                <input
                  type="text"
                  value={draft}
                  onChange={(e) => setDraft(e.target.value)}
                  placeholder="Write a message…"
                  className="h-10 min-w-0 flex-1 rounded-[9px] border border-[#262C38] bg-[#171C26] px-3 text-[13.5px] text-[#F5F6F8] placeholder:text-[#6B7280] outline-none focus:border-[#3B5BFF]"
                  aria-label="Message"
                />
                <button
                  type="submit"
                  disabled={!draft.trim()}
                  className="h-10 rounded-[9px] bg-[#3B5BFF] px-4 text-[13.5px] font-semibold text-white transition-opacity disabled:opacity-40"
                >
                  Send
                </button>
              </form>
            </>
          ) : (
            <div className="flex flex-1 items-center justify-center text-[13px] text-[#6B7280]">
              Select a conversation
            </div>
          )}
        </section>
      </div>
    </div>
  );
}
