# Phases 2–4 Gap Checklist

> **Scope:** Audit/docs only for launch roadmap Phases 2 (Admin), 3 (Payments), 4 (Notifications).  
> **Out of scope:** New features, AI agents, Nice-to-Have items.  
> **Source:** `docs/marketplays_launch_roadmap.md` + evidence in `apps/api` / `apps/web`.  
> **Status legend:** **Done** = implemented end-to-end (or backend contract + enforcement proven). **Partial** = some layer exists (UI stub, service stub, or incomplete path). **Missing** = no meaningful implementation.  
> **API vs UI:** Flags whether closing the gap needs new/changed API endpoints vs UI-only wiring.

---

## Phase 2 — Admin Dashboard

### 2.1 Manage Users

| Item | Status | Evidence | API vs UI |
|------|--------|----------|-----------|
| Approve sellers | **Missing** | No seller-approval field/workflow on `users` (`apps/api/app/models/user.py` has `is_suspended` + Stripe flags only). No admin approve-seller endpoint in `apps/api/app/api/admin.py`. Users page only supports suspend stub UI (`apps/web/src/app/(admin)/admin/users/page.tsx`, `users-table.tsx`). | **Needs new API** (+ likely schema: approval/verification state) + admin UI |
| Suspend users | **Partial** | Schema + auth enforcement: `User.is_suspended` (`models/user.py`); blocked in `apps/api/app/api/deps.py`, `middleware/auth.py`, `auth_service.py`. Admin UI + client stub call `POST /api/admin/users/{id}/suspend` (`admin-api.ts`, `users-table.tsx`) but `adminFetch` never hits the network. **No** `suspend` user route in `apps/api/app/api/admin.py`. | **Needs new API** `POST /api/admin/users/{id}/suspend` (+ audit_logs); UI wire-up only after that |
| Edit listings (admin) | **Missing** | No admin listing edit endpoint; listings admin page is CIS override + stub data only (`admin/listings/page.tsx`, `listings-admin-table.tsx`). Seller listing APIs are not admin edit tools. | **Needs new API** (or admin-authorized PATCH) + UI |
| Verify businesses | **Missing** | No business-verification field/status on `User`/`Listing`. No verify endpoint or admin UI control. (`DeliverableStatus.verified` is proof verification, not business KYC.) | **Needs new API** (+ schema) + UI |

### 2.2 Manage Listings

| Item | Status | Evidence | API vs UI |
|------|--------|----------|-----------|
| Edit | **Missing** | Same as 2.1 edit — no admin edit surface. | **Needs new API** + UI |
| Approve | **Partial** | Moderation queue UI removes row locally only (`moderation-queue.tsx`); no approve API. `ListingStatus` is only `draft` / `published` / `suspended` (`models/enums.py`) — no pending-moderation status. | **Needs new API** (+ possibly status/workflow) + replace stub |
| Reject | **Partial** | Same stub as Approve (`moderation-queue.tsx`); no reject API / audit. | **Needs new API** + replace stub |
| Feature listings | **Missing** | No `is_featured` (or equivalent) on `Listing` model. No feature endpoint or admin control. Roadmap also ties “featured” into revenue KPIs. | **Needs new API** (+ schema) + UI |

### 2.3 Bookings

| Item | Status | Evidence | API vs UI |
|------|--------|----------|-----------|
| View all bookings | **Missing** | No `(admin)/admin/bookings` page. Bookings API is create / get-by-id / review / proof / report-issue only (`apps/api/app/api/bookings.py`) — no admin list-all. | **Needs new API** `GET /api/admin/bookings` (or equivalent) + admin UI page |
| Booking status | **Partial** | Status enum + state machine exist (`domain_enums.py`, `booking_service.py`). Admin can read a single booking if they know the id (`GET /api/bookings/{id}` allows `ADMIN`). No admin list/filter by status. | **Needs list/filter API** + UI (get-by-id alone insufficient) |
| Refunds | **Partial** | Dispute **full** refund calls `stripe_service.refund_payment` then `Disputed → Refunded` (`admin.py`). Cancellation → refund path from rules (`Confirmed → Cancelled` with refund) has **no** dedicated refund orchestration beyond dispute full refund. Partial dispute path adjusts `commission_pence` locally and completes — **does not** call Stripe partial `Refund.create(amount=…)`. Admin refund UI is dispute stub only. | **Needs API work** for cancellation refunds + correct Stripe partial refund; admin refund UX beyond dispute stub |
| Disputes (exactly 3 resolutions) | **Partial** | **API Done (shape):** `POST /api/admin/bookings/{booking_id}/resolve-dispute` with `approve_seller` \| `full_refund` \| `partial_refund` (`schemas/admin.py`, `admin.py`) + `audit_logs` row. **UI Partial:** three actions in `dispute-list.tsx`, but stub `adminFetch`; path/body mismatch vs API (`/api/admin/disputes/{id}/resolve` + `action`/`refund_percent` vs `/bookings/{id}/resolve-dispute` + `resolution`/`partial_percent`). | **UI wiring + contract align**; partial refund Stripe behaviour still needs API fix |

### 2.4 Analytics (admin KPIs)

| KPI | Status | Evidence | API vs UI |
|-----|--------|----------|-----------|
| Users | **Missing** | Not on admin overview KPI row. | **Needs analytics API** + UI |
| Sellers | **Missing** | Not present. | **Needs analytics API** + UI |
| Buyers | **Missing** | Not present. | **Needs analytics API** + UI |
| Listings | **Partial** | Stub “Active listings” count only (`admin/page.tsx` + `STUB_HEALTH`). | **Needs API**; UI exists as stub |
| Bookings | **Missing** | Not a KPI (only “Open disputes” stub). | **Needs analytics API** + UI |
| GMV | **Partial** | Stub “GMV (30 days)” from `stub-data.ts` — not computed from bookings. | **Needs API** (GMV = booking value before commission per roadmap) |
| Revenue | **Missing** | Not shown (revenue = commission + featured + subscriptions per roadmap). | **Needs analytics API** + UI |
| Commission earned | **Missing** | Not shown. | **Needs analytics API** + UI |

No `GET /api/admin/analytics` (or similar) exists under `apps/api/app/api/`.

### Audit logs on every admin mutation

| Item | Status | Evidence | API vs UI |
|------|--------|----------|-----------|
| `audit_logs` table/model | **Done** (schema) | `apps/api/app/models/audit_log.py`; in-memory `store.add_audit_log` (`memory_store.py`). | — |
| Written on dispute resolve | **Done** (API) | `admin.py` → `action="resolve_dispute"`. | UI still stubbed |
| Written on listing suspend | **Done** (API) | `POST /api/admin/listings/{id}/suspend` + audit (`admin.py`). UI stub in `admin-api.ts`. | Wire UI |
| Written on CIS override | **Done** (API) | `cis_service.apply_admin_override` → audit (`cis_service.py`). | Wire UI |
| Written on suspend user / approve|reject listing / feature / admin refunds outside dispute | **Missing** | Endpoints absent or UI-only stubs; cannot satisfy “every mutation writes audit_logs”. | **Needs endpoints** that write audit_logs; UI alone insufficient |

---

## Phase 3 — Payments

| Item | Status | Evidence | API vs UI |
|------|--------|----------|-----------|
| Stripe Connect escrow hold until Completed | **Partial → near Done (service)** | Platform PaymentIntent at create (`stripe_service.create_payment_intent`, `booking_service.create_booking`). Transfer only on `Completed` via `transfer_on_completed` (`stripe_service.py` L190–222, `booking_service.transition` L79–86). Connect account-link stub/live: `POST /api/payments/connect/account-link`. Still mock-capable without keys; end-to-end live Connect not proven by this audit alone. | Mostly **backend Done**; seller/buyer UX already partly present — finish live Connect config/QA, not new product scope |
| Refunds | **Partial** | Full refund helper for dispute path (`refund_payment`). No general cancellation-refund table implementation. Partial dispute does not issue buyer Stripe refund amount. | **Needs API** (cancellation + partial Stripe refund) |
| Failed payments | **Partial** | Webhook dispatches `payment_intent.payment_failed` → `mark_payment_failed` → `Cancelled` (`payments.py`, `booking_service.py`). No dedicated failed-payment buyer messaging/notification beyond cancel transition + logger notify. | Backend path **Done**; buyer UX/email **Missing** (ties to Phase 4) |
| Payout history (seller-facing) | **Missing** | `PendingPayoutCard` + stub amount (`PendingPayoutCard.tsx`, `SELLER_PENDING_PAYOUT_PENCE` in `seller/stub-data.ts`). No payout history list, no API returning transfers/payouts. | **Needs new API** (history of transfers) + UI beyond single stub card |
| Webhook `Stripe-Signature` → HTTP 400 | **Done** | `construct_webhook_event` raises `InvalidStripeSignatureError` on missing/invalid sig (`stripe_service.py` L90–118). Route maps to 400 (`payments.py` L39–44). Tests: `apps/api/tests/test_stripe_webhook.py`. Mock mode still requires non-empty sig and rejects `"invalid"`/`"bad"`/`"unsigned"`. Live mode uses `stripe.Webhook.construct_event` when `STRIPE_SECRET_KEY` + `STRIPE_WEBHOOK_SECRET` set. | Enforced in API — no UI work |

---

## Phase 4 — Notifications

### Seller notifications

| Event | Status | Evidence | API vs UI |
|-------|--------|----------|-----------|
| New booking | **Missing** (real) / **Partial** (log stub) | `notify_booking_created` logs only (`notification_service.py`); called from `booking_service.create_booking`. No in-app row, no email. | **Needs API** + persistence + email provider |
| Booking cancelled | **Missing** | `notify_status_change` logs any status including Cancelled — not seller-specific email/in-app. | **Needs API** + email |
| Payment released | **Missing** | Transfer on Completed calls `notify_booking_completed` (log only) — not a distinct “payment released” channel. | **Needs API** + email |
| Review received | **Missing** | No notify hook on `submit_review` beyond status → Completed path logs. | **Needs API** + email |

### Buyer notifications

| Event | Status | Evidence | API vs UI |
|-------|--------|----------|-----------|
| Booking confirmed | **Missing** | Status change log only (`notify_status_change` after payment succeeded → Confirmed). | **Needs API** + email |
| Campaign live | **Missing** | No Live-specific notification. | **Needs API** + email |
| Campaign complete | **Missing** | `notify_booking_completed` logs seller-oriented message; no buyer in-app/email. | **Needs API** + email |
| Review reminder | **Missing** | No cron/reminder job or notify function. | **Needs API** (+ scheduler) + email |

### Channels & UX

| Item | Status | Evidence | API vs UI |
|------|--------|----------|-----------|
| Email | **Missing** | `notification_service.py` header: “SendGrid wiring TODO”. No SendGrid/Resend client elsewhere in `apps/`. | **Needs API/service** + secrets |
| In-app | **Partial** | Bell dropdown UI with hardcoded stubs (`NotificationPanel.tsx`); mounted in `PortalHeader.tsx`. No `notifications` model/table; no list/mark-read API. | **Needs API** + replace stub data |
| Mark-all-read on dropdown open | **Partial** (UI-only) | Implemented in local React state when opening panel (`NotificationPanel.tsx` `toggleOpen`). Comment notes Section 13 product choice. Not persisted server-side. | **UI Done for stub**; **Needs API** `mark all read` when real notifications exist |

---

## Cross-cutting notes

1. **Admin frontend is stub-first:** `apps/web/src/components/admin/admin-api.ts` explicitly returns `{ stub: true }` and never calls FastAPI. Closing Phase 2 is not “polish” — it requires real fetches + several missing endpoints.
2. **Path/contract drift:** dispute UI targets `/api/admin/disputes/{id}/resolve`; API is `/api/admin/bookings/{booking_id}/resolve-dispute` with different body field names.
3. **Memory store vs SQLAlchemy models:** runtime domain services use `memory_store`; SQLAlchemy models (`audit_logs`, `users.is_suspended`, etc.) exist but admin/payment/notification completeness must be judged against **callable routes + services**, not models alone.
4. **No AI / Nice-to-Have:** this checklist ignores agent tooling and post-launch extras.

---

## Summary counts (roadmap items)

| Phase | Done | Partial | Missing |
|-------|------|---------|---------|
| 2 Admin (user/listing/booking/KPI/audit coverage) | Few API islands (dispute resolve, listing suspend, CIS override, audit model) | Suspend UX, moderation UX, dispute UX, some KPIs, refunds, status read | Approve seller, verify business, feature, edit listing, list-all bookings, most KPIs, full audit coverage |
| 3 Payments | Webhook signature 400 | Escrow/transfer core, failed-payment webhook, dispute full refund | Payout history; cancellation/partial refund completeness |
| 4 Notifications | — | In-app shell + mark-all-read local; logger hooks | All typed email/in-app events + persistence + mark-read API |

---

## Top 5 blockers (Phases 2–4)

1. **Admin mutations are UI stubs with missing endpoints** — suspend user, approve/reject/feature listings, list bookings, and analytics KPIs have no (or incomplete) API; `admin-api.ts` never calls the backend. Phase 2 cannot launch on stubs.
2. **Notifications are logger-only** — no `notifications` persistence, no list/mark-read API, no email provider; required seller/buyer events are unmet despite `NotificationPanel` chrome.
3. **Payments incomplete beyond hold + webhook** — cancellation refunds and correct Stripe partial refunds missing; seller **payout history** is a stub card only.
4. **Admin dispute UI ↔ API contract mismatch** — wrong path and payload vs `resolve-dispute`; until wired, the only fully implemented dispute API is unused by the admin UI.
5. **Audit-log mandate incomplete** — only dispute resolve, listing suspend, and CIS override write `audit_logs`; roadmap-required actions (suspend user, approve/reject, feature, refunds) either lack endpoints or never hit the server, so mutations stay silent or fake.

---

*Generated by Compatibility Agent 4 — Phases 2–4 Gap Audit. No application code changed.*
