# MarketPlays — Functionality Completion Plan (APIs · Backend · Frontend Wiring)
> **Agent-readable reference for Cursor.** Source inputs: `Market-Playzs_Technical_Review_Alpha_Roadmap.docx` (independent technical review, overall 8.2/10) + `MarketPlays_Competitive_Research.docx` (feature gaps vs competitors) + current FastAPI production best practice.
> **Scope of this cycle: finish functionality only.** All remaining APIs, backend logic, and frontend wiring. **Visual polish is explicitly deferred** — do not spend agent time on styling, spacing, or redesign; use whatever components already exist, however rough. Looks get sorted in a later pass.

---

## Table of Contents
- [0. Prime Directive — Do Not Rewrite Existing Code](#0-prime-directive--do-not-rewrite-existing-code)
- [1. What the Technical Review Confirmed](#1-what-the-technical-review-confirmed)
- [2. Workstream A — Finish the Core APIs First](#2-workstream-a--finish-the-core-apis-first)
- [3. Workstream B — New APIs To Build](#3-workstream-b--new-apis-to-build)
- [4. Workstream C — Frontend Wiring (Logic Only, No Styling)](#4-workstream-c--frontend-wiring-logic-only-no-styling)
- [5. Workstream D — Production Readiness](#5-workstream-d--production-readiness)
- [6. Engineering Conventions For All New Code](#6-engineering-conventions-for-all-new-code)
- [7. Suggested Build Order](#7-suggested-build-order)
- [8. Quick Reference](#8-quick-reference)

---

<details>
<summary><strong>0. Prime Directive — Do Not Rewrite Existing Code</strong></summary>

The independent technical review scored the codebase 8.2/10 and was explicit: **the architecture is strong enough to build upon; do not rewrite it.** Monorepo structure (9/10), FastAPI backend with repositories/schemas/middleware/migrations (8.5/10), database entities (8.5/10), Next.js frontend structure (7.5/10), auth foundation (8/10) — all keep as-is.

Rules for every agent working from this file:

- **Extend, never restructure.** New APIs are new router modules + new repository classes following the *existing* repository pattern — do not refactor existing routers, repositories, or middleware to "clean them up" along the way.
- **New tables only where a new feature requires them** (per the review's DB guidance). Never alter existing table columns/types for convenience; additive migrations only.
- **Match existing conventions exactly**: same schema/validation style (Pydantic), same error-handling shape, same auth-dependency pattern, same route naming as the existing listings/bookings/payments routers. If in doubt, copy the pattern of the nearest existing module.
- **Visuals are out of scope.** Frontend tasks in Workstream C mean wiring data, state, and actions into pages that may look unfinished — that's fine. Do not restyle, do not import new UI patterns, do not touch design tokens.
- If any task below appears to require modifying an existing endpoint's contract (request/response shape), stop and flag it to the human instead of changing it — other code already depends on those contracts.

</details>

---

<details>
<summary><strong>1. What the Technical Review Confirmed</strong></summary>

| Area | Score | Directive |
|---|---|---|
| Architecture (monorepo, separation, repository pattern, migrations) | 9/10 | Keep as-is |
| Backend (FastAPI, repositories, schemas, middleware) | 8.5/10 | No rewrite |
| Database (marketplace entities) | 8.5/10 | Add tables only when features require |
| Authentication | 8/10 | Finish verification, password reset, role checks — don't rebuild |
| Frontend (Next.js, buyer/seller/admin routes) | 7.5/10 | Complete functionality; polish UX later |
| Core APIs (auth, listings, bookings, availability, payments, admin) | Exist | **Finish incomplete parts before adding new features** |

Missing before Alpha (review's list): complete buyer journey, seller onboarding, dashboards, messaging, reviews, notifications, responsive polish (polish deferred per Section 0 — everything else is in scope below).

</details>

---

<details>
<summary><strong>2. Workstream A — Finish the Core APIs First</strong></summary>

The review is explicit: *"If the existing payment, booking, listings and availability APIs are incomplete, prioritise finishing those before adding new features."* First task for the agent on this workstream: **audit each core API against its spec and complete the gaps** — do not assume completeness from the file existing.

### A1. Auth completion (review Section 5)
- Email verification flow (send + confirm endpoints) if not complete.
- Phone verification at signup (competitive-research pre-launch item — cheap, standard trust practice). Additive: new verification endpoints + a `phone_verified` flag; do not touch existing auth flow.
- Password reset flow (request + token + reset endpoints).
- Role checks: confirm every protected route actually enforces buyer/seller/admin server-side — an audit-and-fix task, not a redesign.

### A2. Bookings & availability completion
- Verify the full booking status state machine is implemented with all transitions and triggers (webhook, daily cron, admin override) per the existing spec — terminal states truly terminal.
- Availability locking on PaymentIntent creation + 15-minute abandonment release.
- Cancellation/refund policy logic (>7 days 100%, 3–7 days 50%, <3 days 0%, seller-cancels 100%).

### A3. Payments completion
- Stripe Connect escrow end to end (Separate Charges and Transfers): hold until `Completed`/dispute resolution, then transfer minus commission.
- Failed-payment handling; payout-history data endpoint for the seller dashboard.
- Webhook endpoints for all payment events (`payment_intent.succeeded`, `payment_intent.payment_failed`, `transfer.paid`) with signature validation — reject unsigned with 400.

### A4. Listings completion
- Publish guard enforced server-side (Stripe connected + required fields + ≥1 image).
- Draft/suspended exclusion from all buyer queries.

</details>

---

<details>
<summary><strong>3. Workstream B — New APIs To Build</strong></summary>

The review's "API Development Remaining" list, merged with the competitive-research items that need API support. Each is a **new router module + repository following existing patterns**. Suggested endpoints are indicative — match the existing codebase's route-naming style over these exact paths if they differ.

### B1. Reviews & ratings API
- `POST /api/bookings/{id}/review` (if not already complete) — rating 1–5 + comment, only when status = `Awaiting_Buyer_Review`, immutable after submission, triggers CIS recalculation.
- `GET /api/listings/{id}/reviews` — paginated public reviews for the listing page.

### B2. Messaging / conversations API
- `POST /api/conversations` (create thread, buyer↔seller, tied to a listing), `GET /api/conversations` (thread list), `GET /api/conversations/{id}/messages`, `POST /api/conversations/{id}/messages`.
- Record message timestamps per sender → expose a **seller average response time** metric (competitive-research V1.x: feeds CIS breakdown later; build the raw metric now, integration into CIS weighting is a separate decision).
- **Off-platform leakage flagging**: on message create, run a pattern check (phone numbers, emails, "contact me outside" phrasing); set a `flagged` bool for admin moderation — flag, don't block.

### B3. Notifications API (email + in-app)
- `GET /api/notifications` (paginated, unread count), `POST /api/notifications/mark-read` (bulk).
- Server-side event emitters for: new booking, booking cancelled, payment released, review received (seller); booking confirmed, campaign live, campaign complete, review reminder (buyer).
- Email delivery via one transactional provider, called from the same event emitters — heavy sends go through background tasks, not inline in request handlers.

### B4. Saved listings / favourites API
- `POST /api/favourites/{listing_id}`, `DELETE /api/favourites/{listing_id}`, `GET /api/favourites`.

### B5. Search & advanced filtering API
- Complete the filter parameter set on `GET /api/listings` (category, radius/PostGIS, audience, price, availability dates, CIS min, booking type, sort) if any are stubbed.
- Saved searches: `POST /api/saved-searches` (store filter combination), `GET`, `DELETE` — the UI exists in the design reference; this is its data layer.

### B6. Media upload API
- Single upload endpoint handling listing images and proof photos/videos: server-side MIME validation, size caps, storage write, thumbnail generation (background task), returns file URL.
- Reuse for both listing creation and proof-of-play — one module, two callers.

### B7. Seller & buyer verification API
- Seller: business verification submission + admin review status (`pending`/`verified`/`rejected`). Only display "verified" when defensible (competitive-research trust rule).
- Buyer: account-type capture (SME/agency/enterprise) if not already stored.

### B8. Analytics & reporting API
- Buyer: campaign spend over time, active campaigns, avg CIS received.
- Seller: revenue (30-day + 12-month series), occupancy rate, CIS trend, pending payouts.
- These power the existing dashboard pages — read-only aggregate queries, no new business logic.

### B9. Public statistics API
- Featured listings + headline marketplace metrics for the landing pages (listing count, categories) — unauthenticated, cached, minimal fields.

### B10. Audit & moderation + admin reporting endpoints
- Audit log write on every mutating admin action (if any gaps remain) + `GET /api/admin/audit-logs` (filterable).
- Admin listing moderation queue endpoints (approve/reject), dispute queue endpoints (list, resolve: approve-seller / full-refund / partial-refund — exactly three resolutions).
- **Dispute SLA field** (competitive-research V1.x): `first_decision_due_at` timestamp on dispute records (72h from creation for disputes under a value threshold) so the admin UI can show a countdown.
- Admin reporting: users/sellers/buyers/listings/bookings counts, GMV, revenue, commission earned — same definitions as the revenue model (GMV = booking value before commission).

### B11. Attribution API (competitive-research V1.x — build the data layer now, surface later)
- Generate a unique QR/promo code per booking at creation; `GET /api/bookings/{id}/attribution` returns scan/redemption counts; public redirect endpoint records a scan then forwards to the buyer's target URL.

### B12. Coupon / promotion API — **optional, lowest priority; skip if time-constrained** (review marks it optional).

</details>

---

<details>
<summary><strong>4. Workstream C — Frontend Wiring (Logic Only, No Styling)</strong></summary>

Wire existing pages/components to the APIs above. Every task = data fetching, state, actions, error/loading states. Zero styling work.

1. **Buyer journey end to end**: map pins ← listings search API (real data, real filter params); listing detail ← listing + reviews + availability APIs; booking flow → bookings API → Stripe payment element → confirmation ← booking detail API; booking history ← bookings list API.
2. **Seller onboarding**: profile → Stripe Connect redirect → listing create (media upload API) → availability → publish (guard errors surfaced inline).
3. **Dashboards**: buyer campaigns/spend page ← B8 buyer analytics; seller revenue dashboard ← B8 seller analytics + payout history.
4. **Messaging**: thread list + conversation view ← B2; send message action; unread indicators ← notification counts.
5. **Notifications**: bell unread count + dropdown list ← B3; mark-all-read on open.
6. **Reviews**: star-rating prompt on `Awaiting_Buyer_Review` bookings → B1; display stars on completed bookings and listing pages.
7. **Favourites & saved searches**: toggle actions + lists ← B4/B5.
8. **Admin panel**: moderation queue, dispute queue with three resolution actions + SLA countdown, user management, admin analytics ← B10.
9. **Role switching**: header toggle wired to real session role state; switching resets to that role's default page.

</details>

---

<details>
<summary><strong>5. Workstream D — Production Readiness</strong></summary>

From the review's deployment section — required before Alpha exit, buildable in parallel with B/C:

- **Automated tests**: at minimum, integration tests over the two end-to-end journeys (seller: signup→listing→booking→payout; buyer: signup→search→book→pay→review) plus unit tests on the state machine transitions and refund calculator.
- **CI/CD**: pipeline running tests + lint on every PR; deploy previews per branch (Vercel already provides this — wire tests as a required check).
- **Monitoring**: Sentry (errors) + a real health-check endpoint the platform can hit; structured logging with enough context to follow one request through the system — no `print` calls as logging.
- **Backups**: confirm daily Supabase snapshots are enabled + document the restore procedure.
- Caching/background-job infrastructure only where already needed (thumbnails, emails) — the review explicitly says don't add speculative performance infrastructure before growth requires it.

</details>

---

<details>
<summary><strong>6. Engineering Conventions For All New Code</strong></summary>

Grounded in current FastAPI production practice; all additive, none require touching existing code:

- **OpenAPI hygiene**: every new endpoint gets a `summary` and `description` (FastAPI generates the spec from code — write the annotations, they're not optional; agents and humans both read them).
- **Resource-noun routes, HTTP verbs as the action** (`/api/conversations`, not `/api/getConversations`) — consistent with the existing router style.
- **No blocking work in async routes**: emails, thumbnail generation, and any heavy processing go to background tasks; request handlers stay fast.
- **Ownership checks on every route**, not just auth: a buyer can only read their own bookings/conversations; a seller only their own listings/payouts — enforce in the dependency layer per the existing pattern.
- **Pydantic validation at the edge** for every new request body; consistent error response shape matching the existing exception handlers.
- **Dependencies for reusable validation** (e.g. `valid_booking_id`, `conversation_participant`) rather than repeating lookups inline — FastAPI caches dependency results within a request.
- **Additive migrations only**, one migration set per feature branch, never editing a previously applied migration.

</details>

---

<details>
<summary><strong>7. Suggested Build Order</strong></summary>

1. **A (core API completion)** — everything else depends on bookings/payments/listings actually working. Audit first, then fix gaps.
2. **B6 media upload + B1 reviews + B3 notifications** — unblock the most user-visible journeys.
3. **C1–C3, C6, C9** — wire buyer journey, seller onboarding, dashboards, reviews, role switching.
4. **B2 messaging + B4/B5 favourites & saved searches + C4/C5/C7** — engagement layer.
5. **B7/B10 verification, moderation, admin reporting + C8** — admin/trust layer.
6. **B8/B9 analytics + B11 attribution** — reporting layer.
7. **D throughout** — tests written alongside each workstream, not after; CI gate before the Alpha tag.
8. **B12 coupons** — only if everything above is done.

This order matches the review's Alpha → Private Beta progression: core journeys first, engagement features second, admin/trust third, incremental additions after — no architectural rewrites at any stage.

</details>

---

<details>
<summary><strong>8. Quick Reference</strong></summary>

| Need | Where to look |
|---|---|
| The one rule (extend, never rewrite) | Section 0 |
| What's already good — leave alone | Section 1 |
| Core API gaps to close first | Section 2 |
| Full new-API list with endpoints | Section 3 |
| Frontend wiring tasks (no styling) | Section 4 |
| Tests/CI/monitoring before Alpha | Section 5 |
| Conventions for new endpoints | Section 6 |
| What order to build in | Section 7 |

</details>

---

*Functionality completion plan for MarketPlays — APIs, backend, and frontend wiring only; visual polish deferred to a later pass. Pair with `marketplays_cursor_rules.md` (frozen enums/state machine/CIS formula) and `marketplays_6agent_execution_plan.md` if splitting across parallel agents.*
