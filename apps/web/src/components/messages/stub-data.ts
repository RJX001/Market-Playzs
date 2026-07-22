/** Stub message threads — replace with API responses later. */

export interface Message {
  id: string;
  /** true = current logged-in user */
  fromSelf: boolean;
  body: string;
  sentAt: string;
}

export interface MessageThread {
  id: string;
  counterpartName: string;
  listingTitle: string;
  lastPreview: string;
  updatedAt: string;
  unread: boolean;
  messages: Message[];
}

export const STUB_THREADS: MessageThread[] = [
  {
    id: "thr_01",
    counterpartName: "Riverside FC",
    listingTitle: "Pitchside banner — Riverside FC",
    lastPreview: "Proof photo uploaded for the weekend fixture.",
    updatedAt: "2026-07-22T09:40:00Z",
    unread: true,
    messages: [
      {
        id: "msg_01a",
        fromSelf: true,
        body: "Hi — confirming the creative for next Saturday’s match day.",
        sentAt: "2026-07-21T16:10:00Z",
      },
      {
        id: "msg_01b",
        fromSelf: false,
        body: "Received. We’ll install Friday evening ahead of kick-off.",
        sentAt: "2026-07-21T17:02:00Z",
      },
      {
        id: "msg_01c",
        fromSelf: false,
        body: "Proof photo uploaded for the weekend fixture.",
        sentAt: "2026-07-22T09:40:00Z",
      },
    ],
  },
  {
    id: "thr_02",
    counterpartName: "Northstar Agency",
    listingTitle: "Gym entrance screen — Pulse Fitness",
    lastPreview: "Can we extend the booking by one week?",
    updatedAt: "2026-07-21T14:22:00Z",
    unread: false,
    messages: [
      {
        id: "msg_02a",
        fromSelf: false,
        body: "Campaign is performing well — can we extend the booking by one week?",
        sentAt: "2026-07-21T14:22:00Z",
      },
      {
        id: "msg_02b",
        fromSelf: true,
        body: "Yes, the slot is free. I’ll send an amendment once you confirm dates.",
        sentAt: "2026-07-21T15:01:00Z",
      },
    ],
  },
  {
    id: "thr_03",
    counterpartName: "Bean & Co",
    listingTitle: "Café window vinyl — Bean & Co",
    lastPreview: "Thanks — vinyl looks great in the window.",
    updatedAt: "2026-07-20T11:05:00Z",
    unread: false,
    messages: [
      {
        id: "msg_03a",
        fromSelf: true,
        body: "Just checking the vinyl went up on Monday as planned?",
        sentAt: "2026-07-20T10:15:00Z",
      },
      {
        id: "msg_03b",
        fromSelf: false,
        body: "Thanks — vinyl looks great in the window.",
        sentAt: "2026-07-20T11:05:00Z",
      },
    ],
  },
];
