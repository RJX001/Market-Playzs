# Today — Execution matrix (Agents 2–10)

Authoritative cycle plan: `docs/functionality_completion_plan.md`.  
**Prime directive:** EXTEND, never rewrite. Visual polish **OUT OF SCOPE**. **Skip B12 coupons.** Do **not** rebuild auth to Clerk this cycle — finish the existing JWT/bcrypt provider.

This matrix is the collision map. Do not edit files listed under another agent. Import shared glue; do not fork it.

---

## Agent 1 — Coordinator / Integrator (this cycle, already shipping)

| | |
|---|---|
| **Owns (do not touch)** | `docs/today-execution-matrix.md` · `apps/web/src/lib/api.ts` · `apps/web/next.config.ts` · `apps/api/app/api/router.py` · `.github/workflows/ci.yml` · `apps/api/tests/test_e2e_journeys.py` · backups paragraph in `docs/deployment.md` |
| **Role** | Shared frontend client, Next rewrite, optional router includes, CI, journey tests, restore pointer |

**Frontend agents MUST import** `@/lib/api` (`api`, `apiGet`, `apiPost`, `apiPatch`, `apiDelete`). Store the access JWT in `localStorage` key `mp_access_token`. Do not add a second fetch wrapper.

**Backend agents** creating new routers: put `router = APIRouter(...)` in `apps/api/app/api/<module>.py` using the **exact module names** in the optional-include list below. Agent 1 includes them if the module exists; missing modules must not crash the app.

Optional include modules (create these names, nothing else):  
`reviews` · `conversations` · `notifications` · `favourites` · `saved_searches` · `media` · `verification` · `analytics` · `public_stats` · `attribution`

---

## Collision rules (all agents)

- Do not change existing endpoint request/response shapes. If a task seems to require it, stop and flag the human.
- Additive migrations only (one set per feature). Never edit an applied migration.
- New tables only when the feature needs them.
- Money stays integer **pence** in API/DB; format £ only in UI.
- Booking status and category enums are frozen (`docs/marketplays_cursor_rules.md` Section 1.3).
- No restyle, no new design tokens, no layout rewrites.
- OpenAPI: every **new** endpoint gets `summary` and `description`.
- Ownership checks on every new route (not just auth).
- Heavy work (email, thumbnails) via FastAPI `BackgroundTasks`, not inline.
- Do not edit `apps/api/app/api/router.py` — Agent 1 owns includes.

---

## Agent 2 — Auth completion (A1 + login/register wiring + C9)

| | |
|---|---|
| **Workstream** | A1 (finish existing auth). **Not** Clerk. |
| **Owns** | `apps/api/app/api/auth.py` · `apps/api/app/services/auth_service.py` · `apps/api/app/schemas/auth.py` · `apps/api/app/middleware/auth.py` · `apps/api/app/middleware/rate_limit.py` · `apps/api/app/api/deps.py` (role-check audit only) · `apps/api/tests/test_auth.py` · `apps/web/src/app/auth/**` · `apps/web/src/components/shared/RoleToggle.tsx` · `apps/web/src/components/shared/PortalHeader.tsx` |
| **May create** | `apps/api/app/api/verification.py` is **Agent 10**. Agent 2 may add **auth-scoped** verify endpoints under `/api/auth/*` only. Additive columns such as `phone_verified` via a new migration. |
| **Do not touch** | `router.py`, Clerk cutover, `apps/web/src/lib/api.ts` |

### APIs to ship

| Method | Path | Notes |
|---|---|---|
| *(existing)* | `POST /api/auth/register` · `/login` · `/refresh` · `/logout` | Keep contracts. Wire the UI. |
| `POST` | `/api/auth/verify-email` | Send (or resend) verification. |
| `POST` | `/api/auth/verify-email/confirm` | Confirm token. |
| `POST` | `/api/auth/verify-phone` | Signup phone verify (competitive-research). |
| `POST` | `/api/auth/password-reset` | Request reset. |
| `POST` | `/api/auth/password-reset/confirm` | Token + new password. |

Audit: every protected route still uses `require_role` / deps — fix gaps in **deps usage on routes you own**; flag other routers to their owners rather than rewriting them.

### Definition of Done

- [ ] Email verify send + confirm works; unauthenticated confirm is rejected.
- [ ] Phone verify endpoint exists; additive `phone_verified` (do not change existing register body unless purely additive/optional).
- [ ] Password reset request + confirm works; tokens expire.
- [ ] Login/register pages submit via `@/lib/api` and persist `mp_access_token`.
- [ ] Role toggle uses session/role state and navigates to that role’s default page (`/map`, `/dashboard`, `/admin`).
- [ ] Existing auth tests still pass; new tests for verify + reset.
- [ ] No Clerk SDK, no auth-provider rewrite.

---

## Agent 3 — Bookings & availability (A2)

| | |
|---|---|
| **Workstream** | A2 |
| **Owns** | `apps/api/app/api/bookings.py` · `apps/api/app/api/availability.py` · `apps/api/app/services/booking_service.py` · `apps/api/app/schemas/bookings.py` · `apps/api/app/schemas/availability.py` · `apps/api/tests/test_booking_service.py` |
| **May create** | `apps/api/tests/test_refund_calculator.py` (if missing) |
| **Already present — extend, do not duplicate** | `apps/api/app/services/refund_policy.py` (`calculate_refund_pence(*, total_pence, cancelled_by, start_date, today=None) -> tuple[int, int]`) |
| **May touch (minimal)** | Cron stubs in `apps/api/app/main.py` (`/api/cron/booking-transitions`, `/api/cron/extend-availability`) — call into `booking_service` / availability; do not rewrite the FastAPI app. |
| **Do not touch** | `payments.py`, `stripe_service.py`, `admin.py`, `listings.py` |

`POST /api/bookings/{id}/review` already lives on `bookings.py`. **You own it.** Complete immutability + `Awaiting_Buyer_Review` guard if any gap remains. Agent 6 owns **listing** review list only (`GET /api/listings/{id}/reviews`).

### APIs to ship

| Method | Path | Notes |
|---|---|---|
| *(existing)* | `POST /api/bookings` · `GET /api/bookings/{id}` · `POST /api/bookings/{id}/review` · `/proof` · `/report-issue` | Finish gaps; no client `PATCH` status. |
| `GET` | `/api/bookings` | List current user’s bookings (buyer = own, seller = own listings). Missing today. |
| `POST` | `/api/bookings/{id}/cancel` | Cancellation + refund policy (see calculator). |
| *(existing)* | `GET/POST /api/availability/{listing_id}` | 15-minute lock release on abandoned `Pending_Payment`. |

**Refund calculator** already lives at `apps/api/app/services/refund_policy.py` — **extend it, do not add a second module**. Agent 1 e2e imports `calculate_refund_pence` from there.

Policy: buyer cancel **>7 days → 100%**, **3–7 days → 50%**, **<3 days → 0%**; **seller-cancels → 100%**. `cancelled_by` is `"buyer"` or `"seller"`.

State machine: all Section 5.2 transitions + triggers (webhook already Agent 4; daily cron; admin override stays Agent 10). Terminal states stay terminal.

### Definition of Done

- [ ] Full status machine implemented; invalid/terminal transitions raise `InvalidTransitionError`.
- [ ] Availability locked on PaymentIntent creation; abandoned `Pending_Payment` released after 15 minutes (cron or equivalent).
- [ ] `refund_policy.calculate_refund_pence` remains the single calculator; cancel endpoint uses it.
- [ ] `GET /api/bookings` list is ownership-scoped.
- [ ] Daily cron stub calls real transition helpers.
- [ ] `test_booking_service` + refund unit tests pass. Agent 1 e2e no longer skips the refund test.

---

## Agent 4 — Payments (A3)

| | |
|---|---|
| **Workstream** | A3 |
| **Owns** | `apps/api/app/api/payments.py` · `apps/api/app/services/stripe_service.py` · `apps/api/tests/test_stripe_webhook.py` |
| **Do not touch** | `booking_service.py` (call into it; don’t relocate state machine), `admin.py` dispute refunds (Agent 10 may call `stripe_service`) |

### APIs to ship

| Method | Path | Notes |
|---|---|---|
| *(existing)* | `POST /api/payments/webhook` | Signature **required**; unsigned → **400**. Handle `payment_intent.succeeded`, `payment_intent.payment_failed`, `transfer.paid`. |
| *(existing)* | `POST /api/payments/connect/account-link` | Finish Connect onboarding link if stubbed. |
| `GET` | `/api/payments/payouts` | Seller payout history (read-only). Seller role + ownership. |

Escrow: hold until `Completed` / dispute resolution; transfer minus commission (already sketched in `booking_service.transition` → `stripe_service.transfer_on_completed`). Failed-payment → existing `mark_payment_failed`. Partial Stripe refund helper if Agent 10 dispute `partial_refund` needs `Refund.create(amount=…)`.

### Definition of Done

- [ ] Webhook rejects missing/invalid signature with 400.
- [ ] All three event types handled (ack unknown types with 200).
- [ ] Seller `GET /api/payments/payouts` returns a stable list shape (pence integers).
- [ ] Connect account-link returns a URL a seller frontend can redirect to.
- [ ] Webhook tests cover 400 on bad signature + succeeded/failed dispatch.

---

## Agent 5 — Listings + media + search filters (A4, B5 filters, B6)

| | |
|---|---|
| **Workstream** | A4, B5 (filter params on listings), B6 |
| **Owns** | `apps/api/app/api/listings.py` · `apps/api/app/services/listing_service.py` · `apps/api/app/schemas/listings.py` · `apps/api/tests/test_filter_logic.py` |
| **Must create** | `apps/api/app/api/media.py` (**module name `media`**) · `apps/api/app/services/media_service.py` · schemas/repo as needed |
| **Do not touch** | Seller wizard UI (Agent 9). Saved-search CRUD (Agent 6). |

### APIs to ship

| Method | Path | Notes |
|---|---|---|
| *(existing)* | `GET /api/listings` | Complete filters: category, radius/PostGIS, audience, price, availability dates, CIS min, booking type, sort. Draft/suspended **never** in buyer results. |
| *(existing)* | `GET/POST/PATCH /api/listings` · `POST /api/listings/{id}/publish` | Publish guard: Stripe connected + required fields + ≥1 image — **server-side**. |
| `POST` | `/api/media/upload` | Listing images **and** proof photos/videos. MIME + size validation, storage write, thumbnail via background task, returns `{ url }`. |

### Definition of Done

- [ ] Publish without Stripe / fields / image is 400 with a clear `detail`.
- [ ] Buyer search never returns `draft` or `suspended`.
- [ ] Filter query params documented on the OpenAPI operation.
- [ ] Single upload endpoint reused conceptually for listings + proof (proof **transition** stays Agent 3 `POST /bookings/{id}/proof`).
- [ ] `media.py` exports `router` so Agent 1 include succeeds.
- [ ] Filter tests updated for any newly enforced params.

---

## Agent 6 — Reviews list, favourites, saved searches (B1 GET, B4, B5 saved)

| | |
|---|---|
| **Workstream** | B1 (listing reviews), B4, B5 saved searches |
| **Must create** | `apps/api/app/api/reviews.py` · `apps/api/app/api/favourites.py` · `apps/api/app/api/saved_searches.py` · matching schemas/repos/tests |
| **Do not touch** | `bookings.py` (review POST is Agent 3). `listings.py` (do not add `/{id}/reviews` there — use `reviews` module). Buyer UI (Agent 8). |

### APIs to ship

| Method | Path | Notes |
|---|---|---|
| `GET` | `/api/listings/{id}/reviews` | Paginated public reviews. Router lives in `reviews.py`. |
| `POST` | `/api/favourites/{listing_id}` | Auth buyer. |
| `DELETE` | `/api/favourites/{listing_id}` | |
| `GET` | `/api/favourites` | Current user. |
| `POST` | `/api/saved-searches` | Store filter combination. |
| `GET` | `/api/saved-searches` | |
| `DELETE` | `/api/saved-searches/{id}` | Ownership required. |

### Definition of Done

- [ ] Three modules export `router` with the names above (`saved_searches` module → paths `/api/saved-searches`).
- [ ] Favourites are per-user; deleting someone else’s favourite is 403/404.
- [ ] Saved searches persist filter payload the buyer UI already shapes (see `use-saved-searches.ts`) — replace localStorage later in Agent 8, don’t invent a parallel schema.
- [ ] Review list is public, paginated, ordered newest-first.
- [ ] Tests for happy path + ownership.

---

## Agent 7 — Messaging + notifications (B2, B3 + C4, C5)

| | |
|---|---|
| **Workstream** | B2, B3, C4, C5 |
| **Owns** | `apps/api/app/services/notification_service.py` (**extend**) |
| **Must create** | `apps/api/app/api/conversations.py` · `apps/api/app/api/notifications.py` · services/schemas/repos/tests |
| **Frontend** | `apps/web/src/app/messages/**` · `apps/web/src/components/messages/**` · `apps/web/src/components/shared/NotificationPanel.tsx` |
| **Do not touch** | `booking_service.py` except calling `notification_service` emitters if you add hooks there — prefer emitting from notification_service functions that Agent 3 already calls (`notify_booking_created`, `notify_status_change`, `notify_booking_completed`). Extend those. |

### APIs to ship

| Method | Path | Notes |
|---|---|---|
| `POST` | `/api/conversations` | Buyer↔seller thread tied to a listing. |
| `GET` | `/api/conversations` | Thread list for current user. |
| `GET` | `/api/conversations/{id}/messages` | Participants only. |
| `POST` | `/api/conversations/{id}/messages` | Off-platform leakage: set `flagged` bool (do **not** block). Record timestamps for seller avg response time. |
| `GET` | `/api/notifications` | Paginated + unread count. |
| `POST` | `/api/notifications/mark-read` | Bulk mark-read. |

Emitters (email via one provider + in-app row): new booking, booking cancelled, payment released, review received (seller); booking confirmed, campaign live, campaign complete, review reminder (buyer). Email in background tasks.

### Definition of Done

- [ ] Conversation participants only; non-participant → 403.
- [ ] Message create runs leakage pattern check; `flagged` stored for admin.
- [ ] Seller average response time is computable from message timestamps (expose on thread or a small metric field).
- [ ] Notifications list + unread count; mark-read clears unread.
- [ ] Messages UI and NotificationPanel fetch via `@/lib/api` (loading/error/empty states). **No styling pass.**
- [ ] Modules `conversations` and `notifications` export `router`.

---

## Agent 8 — Buyer frontend wiring (C1, C3 buyer, C6, C7)

| | |
|---|---|
| **Workstream** | C1, C3 (buyer campaigns/spend), C6, C7 |
| **Owns** | `apps/web/src/app/(buyer)/**` · `apps/web/src/components/buyer/**` · `apps/web/src/app/listings/[id]/page.tsx` · `apps/web/src/hooks/useBooking.ts` · `apps/web/src/hooks/useMap.ts` |
| **Do not touch** | Mock-data files may remain as fallback but live path must call APIs. Do not restyle. Do not edit `api.ts`. |

Wire to Agent 3/4/5/6/10 APIs as they land. Use `@/lib/api`. Relative `/api/*` is rewritten locally (Next config).

### Must wire

1. Map pins ← `GET /api/listings` with real filter params (sidebar already has the controls).
2. Listing detail + slide-in ← listing + `GET /api/listings/{id}/reviews` + availability.
3. Book → `POST /api/bookings` → Stripe Payment Element using `client_secret` → confirmation from `GET /api/bookings/{id}`.
4. Booking / campaign history ← `GET /api/bookings` (and B8 buyer analytics when Agent 10 ships).
5. Star-rating prompt when status is `Awaiting_Buyer_Review` → `POST /api/bookings/{id}/review`.
6. Favourites toggle + saved searches ← B4/B5 (replace localStorage in `use-saved-searches.ts` when API exists).

### Definition of Done

- [ ] Map/search/detail/book/pay/confirm/history no longer depend on mock as the happy path (fallback only if API errors).
- [ ] `useBooking` uses `@/lib/api` (Bearer + credentials); does not treat 404 as success once the API is up.
- [ ] Review CTA only for `Awaiting_Buyer_Review` owned by the buyer.
- [ ] Favourites + saved searches call APIs when present.
- [ ] Loading and error states exist. **Zero visual polish.**

---

## Agent 9 — Seller frontend wiring (C2, C3 seller)

| | |
|---|---|
| **Workstream** | C2, C3 seller dashboard |
| **Owns** | `apps/web/src/app/(seller)/**` · `apps/web/src/components/seller/**` |
| **Do not touch** | `ListingWizard` restyle. Payments backend (Agent 4). Media backend (Agent 5). |

### Must wire

1. Profile / register-seller already Agent 2 — seller **onboarding checklist**: Stripe Connect redirect (`POST /api/payments/connect/account-link`) → listing create → `POST /api/media/upload` → availability → publish. Surface publish-guard errors inline (`PublishGuard.tsx`).
2. Seller dashboard ← `GET` B8 seller analytics (Agent 10) + `GET /api/payments/payouts`. Existing cards (`RevenueChart`, `PendingPayoutCard`, `OccupancyHeatmap`, `CisBreakdownCard`) should consume API data, not only `stub-data.ts`.
3. Listings list/edit/new ← listings CRUD + media.

### Definition of Done

- [ ] Seller can create a draft, upload ≥1 image, set availability, hit publish, and see guard errors from the API.
- [ ] Connect redirect round-trip works against the account-link endpoint.
- [ ] Dashboard KPIs/charts/payouts use API JSON (pence → £ at the edge).
- [ ] Bookings page uses `GET /api/bookings` (seller scope).
- [ ] Import `@/lib/api` only. No styling.

---

## Agent 10 — Admin, trust, analytics, public stats, attribution (B7–B11 + C3 data + C8)

| | |
|---|---|
| **Workstream** | B7, B8, B9, B10, B11, C8 (admin UI logic) |
| **Owns** | `apps/api/app/api/admin.py` · `apps/api/app/schemas/admin.py` · `apps/api/app/models/audit_log.py` · `apps/web/src/app/(admin)/**` · `apps/web/src/components/admin/**` (including replace stub `admin-api.ts` with `@/lib/api`) |
| **Must create** | `apps/api/app/api/verification.py` · `apps/api/app/api/analytics.py` · `apps/api/app/api/public_stats.py` · `apps/api/app/api/attribution.py` |
| **Skip** | **B12 coupons** |
| **Do not touch** | `bookings.py` state machine; call `booking_service.transition` for dispute outcomes. |

### APIs to ship

| Method | Path | Notes |
|---|---|---|
| `POST` / `GET` | `/api/verification/seller` (and admin review) | Status `pending` / `verified` / `rejected`. Show “verified” only when defensible. |
| `POST` / `PATCH` | buyer account-type (SME/agency/enterprise) | Additive on user if not stored. |
| `GET` | `/api/analytics/buyer` | Spend over time, active campaigns, avg CIS received. |
| `GET` | `/api/analytics/seller` | Revenue 30-day + 12-month, occupancy, CIS trend, pending payouts. |
| `GET` | `/api/public/stats` | Unauthenticated, cached: listing count, categories, featured listings (minimal fields). |
| `GET` | `/api/admin/audit-logs` | Filterable. Mutating admin actions already write audit rows — fill gaps. |
| | Admin moderation queue approve/reject listings | Extend `admin.py`. |
| *(existing)* | `POST /api/admin/bookings/{id}/resolve-dispute` | Keep **three** resolutions: `approve_seller` / `full_refund` / `partial_refund`. Add `first_decision_due_at` (72h) on dispute records. Align frontend `admin-api.ts` to **this** contract (it currently posts a different path). |
| `GET` | `/api/admin/reporting` | Users/sellers/buyers/listings/bookings counts, GMV, revenue, commission (GMV = booking value **before** commission). |
| | Attribution | Unique QR/promo code per booking at creation; `GET /api/bookings/{id}/attribution`; public redirect records scan then forwards. Implement in `attribution.py` (not by rewriting `bookings.py` — include extra routes on the attribution router). |

### Definition of Done

- [ ] Modules `verification`, `analytics`, `public_stats`, `attribution` export `router`.
- [ ] Admin UI: moderation queue, dispute queue with three actions + SLA countdown, users, reporting — all via `@/lib/api`.
- [ ] Dispute UI path/body matches `admin.py` (`resolution`, `partial_percent`) — do not invent a second contract.
- [ ] Public stats safe for the marketing homepage (Agent 8/9 may consume; you may wire `apps/web/src/app/page.tsx` **data only** if needed — no redesign).
- [ ] B12 not started.

---

## Suggested parallel batches

| Batch | Agents | Why |
|---|---|---|
| 1 | 2, 3, 4, 5 | Core APIs (A) + media. Unblocks journeys. |
| 2 | 6, 7, 10 | New B routers (includes no-op until files exist). |
| 3 | 8, 9 | Frontend wiring against live APIs + `@/lib/api`. |

Agent 8/9 can start against existing listings/bookings/payments immediately; treat missing B-* routers as empty/error states.

---

## Out of scope this cycle

- Visual polish / redesign / new UI kits
- Clerk migration (`docs/clerk-migration-plan.md` stays parked)
- B12 coupon / promotion API
- In-product AI agents
- Rewrites of repository pattern, middleware, or existing contracts
