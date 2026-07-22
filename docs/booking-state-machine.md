# Marketplays — Booking State Machine

Authoritative source: `docs/marketplays_cursor_rules.md` **Section 5.2**.  
Status enum values (Section 1.3): `Pending_Payment`, `Confirmed`, `Live`, `Awaiting_Proof`, `Awaiting_Buyer_Review`, `Completed`, `Cancelled`, `Refunded`, `Disputed`, `Admin_Flagged`.

Only the system (cron, Stripe webhook, or an explicit admin override) may transition `bookings.status`. Clients never PATCH `status` directly.

---

## Valid transitions

| From | To | Trigger |
|------|-----|---------|
| `Pending_Payment` | `Confirmed` | Stripe `payment_intent.succeeded` |
| `Pending_Payment` | `Cancelled` | Payment abandoned 15 min, or `payment_failed` |
| `Confirmed` | `Live` | Campaign `start_date` reached (daily cron 00:01) |
| `Confirmed` | `Cancelled` | Buyer/seller cancels pre-start — refund triggered |
| `Live` | `Awaiting_Proof` | Campaign `end_date` reached (daily cron) |
| `Live` | `Disputed` | Admin action |
| `Awaiting_Proof` | `Awaiting_Buyer_Review` | Seller uploads proof |
| `Awaiting_Proof` | `Admin_Flagged` | 48 hr timeout, no proof |
| `Awaiting_Buyer_Review` | `Completed` | Buyer submits rating, **or** 72 hr auto-approve timeout (rating defaults to 3) |
| `Awaiting_Buyer_Review` | `Disputed` | Buyer clicks Report Issue |
| `Disputed` | `Completed` | Admin: approve seller, full or partial payout |
| `Disputed` | `Refunded` | Admin: full refund |

---

## Diagram

```
Pending_Payment ──[payment_intent.succeeded]──► Confirmed
Pending_Payment ──[abandoned 15min / payment_failed]──► Cancelled

Confirmed ──[start_date, cron 00:01]──► Live
Confirmed ──[cancel pre-start + refund]──► Cancelled

Live ──[end_date, daily cron]──► Awaiting_Proof
Live ──[admin]──► Disputed

Awaiting_Proof ──[seller uploads proof]──► Awaiting_Buyer_Review
Awaiting_Proof ──[48hr timeout]──► Admin_Flagged

Awaiting_Buyer_Review ──[rating OR 72hr auto-approve]──► Completed
Awaiting_Buyer_Review ──[Report Issue]──► Disputed

Disputed ──[admin: approve seller]──► Completed
Disputed ──[admin: full refund]──► Refunded
```

---

## Terminal states

`Completed`, `Cancelled`, and `Refunded` are **terminal**.

- No further transitions, including by admin override tooling.
- A correction requires a new booking or a documented manual ledger adjustment — never mutate a terminal status.

---

## Notes outside Section 5.2

`Admin_Flagged` is a reachable status from `Awaiting_Proof` (48 hr timeout). Section 5.2 does not define outbound transitions from `Admin_Flagged`; admin resolution tooling must be specified separately before adding edges.
