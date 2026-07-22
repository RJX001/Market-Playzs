# Marketplays — Cursor Master Rules
> **Agent-readable reference — feed this whole file to Cursor before Prompt 1.** Every rule a build agent needs, in one place, organised as collapsible sections so any single agent (or sub-agent) can be pointed at just the section it needs.
> Companion docs: `marketplays_cursor_build_guide.md` (visual/design build guide), `marketplays_ai_agents_architecture.md` (in-product agent deep-dive), `Marketplays_Developer_Specification.docx` (original functional spec).

---

## Table of Contents
- [0. How To Use This File](#0-how-to-use-this-file)
- [1. Global Rules](#1-global-rules)
- [2. Deployment & Hosting Rules](#2-deployment--hosting-rules)
- [3. Design System Rules](#3-design-system-rules)
- [4. Database Schema Rules](#4-database-schema-rules)
- [5. Backend / API Rules](#5-backend--api-rules)
- [6. Buyer Portal Rules](#6-buyer-portal-rules)
- [7. Seller Portal Rules](#7-seller-portal-rules)
- [8. Admin Portal Rules](#8-admin-portal-rules)
- [9. AI Agent Rules](#9-ai-agent-rules)
- [10. Quick Reference](#10-quick-reference)

---

<details>
<summary><strong>0. How To Use This File</strong></summary>

- Paste **Section 1 (Global) + Section 2 (Deployment)** into every Cursor agent's context, every prompt, no exceptions — these are load-bearing and cheap to include.
- Paste **Section 3 (Design)** into any prompt touching UI (both portals, landing pages).
- Paste **Section 4 (Database) + Section 5 (Backend/API)** into any prompt touching FastAPI, Supabase, or Stripe.
- Paste **Section 6 / 7 / 8** into the matching portal-specific prompt only — don't load Seller rules into a Buyer-portal agent run, it wastes context and risks cross-contamination of UI patterns.
- Paste **Section 9 (AI Agents)** only once you reach the V1.1+ agent-layer build prompts — not during MVP scaffolding.
- If a rule here ever conflicts with a rule in the original spec doc, **this file wins** — it reflects the latest decisions (hosting, design tokens from the approved mockups) that postdate the original spec.

</details>

---

<details>
<summary><strong>1. Global Rules</strong></summary>

### 1.1 Tech stack (authoritative — do not substitute)

| Layer | Choice |
|---|---|
| Frontend | Next.js 15 (App Router), shadcn/ui, Tailwind CSS |
| Backend | FastAPI (Python) |
| Database | Supabase (PostgreSQL + PostGIS) |
| Payments | Stripe Connect — Separate Charges and Transfers |
| Mapping | Mapbox GL JS |
| Hosting — frontend | Vercel |
| Hosting — backend | **Vercel** (Python runtime / Vercel Functions) — see Section 2, this changed from the original Railway plan |
| DNS / domain | Cloudflare (registrar + DNS manager, **proxy set to DNS-only**, not proxied) — see Section 2 |
| In-product AI agents (V1.1+) | PydanticAI (backend supervisor/sub-agents), Vercel AI SDK 6 (frontend chat/tool-loop UI), MCP (tool exposure) |
| Build tooling | Cursor (agentic build), ChatGPT (planning/review) |

### 1.2 Repo conventions

- Monorepo: `apps/web` (Next.js), `apps/api` (FastAPI), `packages/` for shared types/config if needed.
- One shared `category` enum used identically by frontend, backend, and DB — see Section 3.5 / Section 4.
- Never hand-roll a colour, spacing, or component that Section 3 already defines — extend, don't reinvent.
- Environment variables: never commit `.env`; Stripe secret keys, Supabase service role key, Mapbox secret token all server-side only, never exposed to the Next.js client bundle.
- All money values stored as integers in minor units (pence) in the DB; format to £ only at the presentation layer.

### 1.3 Naming

- Booking status enum values are exactly: `Pending_Payment`, `Confirmed`, `Live`, `Awaiting_Proof`, `Awaiting_Buyer_Review`, `Completed`, `Cancelled`, `Refunded`, `Disputed`, `Admin_Flagged` — never invent alternate casing or synonyms anywhere in code, UI copy, or agent tool schemas.
- Category enum values are exactly: `sports_club`, `gym`, `school`, `shop`, `cafe`, `festival`, `community_event`, `billboard`, `event_venue` — extendable later, but agents and UI must read from one shared source, not redefine locally.

</details>

---

<details>
<summary><strong>2. Deployment &amp; Hosting Rules</strong></summary>

### 2.1 Decision (confirmed)

Both the Next.js frontend and the FastAPI backend deploy to **Vercel** — not Railway. Rationale: Vercel has official first-class FastAPI support via the Python runtime / Vercel Functions (confirmed current as of July 2026), and running both on one platform simplifies the deploy pipeline for a solo/small-team build.

### 2.2 Two-project structure

- `marketplays-web` (Vercel project) — Next.js frontend, domain `marketplays.com` + `www.marketplays.com`.
- `marketplays-api` (separate Vercel project) — FastAPI backend, domain `api.marketplays.com`.
- Do **not** collapse these into one Vercel project unless a specific reason emerges — separate projects mean independent scaling, independent logs, independent Fluid Compute settings, and no risk of a heavy agent-orchestration request blocking frontend static asset serving.

### 2.3 FastAPI entrypoint rules (Vercel Python runtime)

- FastAPI instance must be named `app` at a supported entrypoint: `app.py`, `index.py`, `server.py`, `main.py`, `wsgi.py`, or `asgi.py`.
- If using a custom path, set `tool.vercel.entrypoint` in `pyproject.toml` — don't rely on Vercel guessing.
- Bundle size limit: 500MB standard; up to 5GB only if Fluid Compute (Large Functions) is explicitly enabled — check this before adding heavy ML/image-processing dependencies.
- Cron jobs (90-day availability window extension, daily booking-state-machine transitions per Section 5.4) run via **Vercel Cron** (`vercel.json` `crons` array) — not a separate scheduler service.
- **Do not** put long-running or queue-style work (proof-video processing, malware scanning on uploads, multi-step AI agent chains that risk execution-time limits) directly in a Vercel Function. Route these to a small dedicated worker (Railway free tier, or a queue service like Inngest/QStash) — Vercel Functions are request/response, not persistent workers.

### 2.4 DNS — Cloudflare (confirmed setup)

- Cloudflare remains the domain registrar **and** DNS manager. Do **not** migrate nameservers to Vercel.
- In Cloudflare DNS tab, add exactly the records Vercel specifies when you add the domain in Vercel project settings (typically an A record for the apex domain and a CNAME for `www`, plus a separate CNAME for `api` pointing at the `marketplays-api` Vercel project).
- **Every one of those records must be set to "DNS only" (grey cloud), never "Proxied" (orange cloud).** Proxying through Cloudflare in front of Vercel breaks Vercel's automatic SSL issuance/renewal and degrades Vercel's bot protection — this is Vercel's own current guidance, not a workaround.
- If a "too many redirects" error appears, check Cloudflare SSL/TLS mode is set to **Full** (not Flexible) — this is the most common cause.
- Do not enable Cloudflare's own proxy-level caching, WAF, or Bot Fight Mode against Marketplays traffic while DNS-only — those features require proxy mode and are off the table under this setup. If they're needed later, that's a deliberate follow-up decision, not a default.

### 2.5 Environment separation

- `preview` deployments (Vercel preview URLs per PR/branch) use a separate Supabase project or schema and Stripe **test mode** keys — never point a preview deployment at production Stripe or production Supabase.
- Production Stripe webhook endpoint and Supabase URL only ever configured against the `production` Vercel environment variables, not `preview`/`development`.

</details>

---

<details>
<summary><strong>3. Design System Rules</strong></summary>
*(Condensed from `marketplays_cursor_build_guide.md` Section 2 — full detail there; this is the enforceable subset.)*

### 3.1 Colour tokens (CSS variables — define once, reference everywhere)

```css
--brand-blue: #1A56DB;
--pin-available: #22C55E;
--pin-limited: #F59E0B;
--pin-booked: #EF4444;
--pin-new: #7C3AED;
```

- CIS badge colour always follows the score band (90–100 excellent/green → 0–59 at-risk/red → null/grey "New"), never a fixed colour independent of score.
- Marketing pages (landing) are **light mode**. Logged-in app (buyer/seller dashboards) is **dark mode**. Do not mix — a dashboard screen must never render on a light background and vice versa.

### 3.2 Component reuse rules (do not fork)

- `<ListingSlideInPanel>` is used identically across: landing-page map preview, buyer dashboard map, and (read-only variant) booking confirmation page. One component, prop-driven, not three implementations.
- `<HeroSplit>` and `<CategoryShowcaseCard>` are shared between the Buyer landing page and Seller landing page — different copy/data props, same component.
- KPI cards (both dashboards) are one `<KpiCard>` component: large value, small muted label, optional coloured trend delta.
- Booking status pills map 1:1 to the booking status enum in Section 1.3 — never introduce a UI-only status label that doesn't exist in the enum.

### 3.3 Copy tone rules

- Marketing headlines: 4–6 words, outcome-first, sentence case (e.g. "Grow Locally with Measurable Presence").
- Every hero has exactly 3 bullet points, each verb + outcome, no more, no fewer.
- Dashboard microcopy: number leads, label is secondary — never invert this hierarchy.

### 3.4 Hidden dev-only chrome

- Any debug/breadcrumb label seen in design mockups (e.g. "Buyer dashboard — live map view") is a design-review artifact, not production UI — must sit behind a debug flag or be removed entirely before shipping.

### 3.5 Category taxonomy

- Use the exact enum in Section 1.3. The icon set on the buyer landing page category strip (Sports Club, Gym, School, Shop, Café, Festival, "…" overflow) must map 1:1 to this enum — no orphan icons without a backing enum value, no enum values without an icon.

</details>

---

<details>
<summary><strong>4. Database Schema Rules</strong></summary>
*(Full field list in `Marketplays_Developer_Specification.docx` Section 10 — these are the enforceable constraints.)*

- All tables include `created_at` and `updated_at` timestamps — no exceptions.
- `listings.cis_score` is nullable (null = "New", not zero) — never default it to 0.
- `listings.is_cis_overridden` (bool) must be set alongside any admin manual CIS edit, and the edit must also write an `audit_logs` row — an override without an audit log entry is a bug.
- `availability` is one row per date per listing — never store date ranges as a single row; the 90-day rolling window and per-date lock/unlock logic depends on row-per-date granularity.
- `bookings.status` uses exactly the 9 enum states in Section 1.3 (originally documented as 9; note `Admin_Flagged` and `Disputed` are both reachable, giving effectively 10 — treat the full list in Section 1.3 as authoritative over any earlier "9 states" count).
- `reviews.delivery_score` is one of exactly `0`, `0.5`, `1` (never a free float) — this feeds the CIS formula directly (Section 5.3).
- `deliverables.status` enum: `pending`, `uploaded`, `verified` — a proof upload moves `pending → uploaded`; only admin action moves `uploaded → verified` in dispute contexts.
- Extend `audit_logs` with `initiated_by_agent` (bool, default `false`) and `agent_session_id` (nullable) ahead of the V1.1 agent build (Section 9) — add this column now even if unused until then, to avoid a later migration touching a table with live audit history.
- New table required for the agent layer: `buyer_agent_policies` (buyer/org id, max_per_booking_value, max_monthly_agent_spend) — see Section 9.4.

</details>

---

<details>
<summary><strong>5. Backend / API Rules</strong></summary>

### 5.1 Security (non-negotiable)

- JWT: 15-minute access token, 7-day refresh token, refresh token in HttpOnly cookie only.
- bcrypt cost factor 12 minimum for password hashing. Never log or return password hints.
- Role-based middleware on every protected route — buyer cannot reach seller endpoints and vice versa, enforced server-side, not just hidden in UI.
- Every Stripe webhook handler validates the `Stripe-Signature` header and rejects unsigned events with HTTP 400 — no exceptions, including in preview/test environments.
- Parameterised queries only (SQLAlchemy ORM) — never string-interpolate user input into raw SQL.
- Rate limits: login endpoint 5 attempts/IP/15min; global API 100 req/min per authenticated user.
- File uploads: validate MIME type server-side (not just extension), scan for malware before serving, enforce max size server-side regardless of client-side checks.

### 5.2 Booking state machine (authoritative transitions)

Only these transitions are valid, and only the system (cron, webhook, or an explicit admin override) may trigger them — never a direct client PATCH to `status`:

```
Pending_Payment → Confirmed         [Stripe payment_intent.succeeded]
Pending_Payment → Cancelled         [payment abandoned 15min, or payment_failed]
Confirmed       → Live              [campaign start_date reached, daily cron 00:01]
Confirmed       → Cancelled         [buyer/seller cancels pre-start — refund triggered]
Live            → Awaiting_Proof    [campaign end_date reached, daily cron]
Live            → Disputed          [admin action]
Awaiting_Proof  → Awaiting_Buyer_Review  [seller uploads proof]
Awaiting_Proof  → Admin_Flagged     [48hr timeout, no proof]
Awaiting_Buyer_Review → Completed   [buyer submits rating, OR 72hr auto-approve timeout — rating defaults to 3]
Awaiting_Buyer_Review → Disputed    [buyer clicks Report Issue]
Disputed        → Completed         [admin: approve seller, full or partial payout]
Disputed        → Refunded          [admin: full refund]
```

`Completed`, `Cancelled`, `Refunded` are terminal — no further transitions, ever, including by admin override tooling (a correction requires a new booking or a documented manual ledger adjustment, not a terminal-state mutation).

### 5.3 CIS formula (authoritative)

```
delivery_component = delivery_score * 0.5     // delivery_score: 1 on-time, 0.5 late, 0 not uploaded
rating_component   = (rating / 5) * 0.5       // rating: buyer's 1–5 stars
new_booking_cis     = (delivery_component + rating_component) * 100
listing_cis         = AVG(cis_score) across all Completed bookings for that listing, rounded to nearest integer
```

Recalculates within 60 seconds of: buyer rating submitted, 72hr auto-approve timeout, or admin override. CIS is per-listing, never per-seller.

### 5.4 Filter logic

- All buyer map filters are AND conditions across filter types, OR within a multi-select filter (e.g. multiple asset types OR'd together, then AND'd with price range, AND'd with location radius, etc.).
- Empty filter request → return all published, non-draft listings in the default viewport bounding box — never return zero results for an empty filter set.
- Listings with null CIS are included in all CIS filter tiers by default (flagged "New Listing" in UI), not excluded.
- Draft and suspended listings are never returned in buyer queries, regardless of any other filter or rank score.

### 5.5 Key endpoints (see spec doc Section 11 for the full list — do not duplicate logic between endpoints and any AI agent tool wrapper; the agent tool must call these same endpoints, never bypass them)

- `POST /api/bookings` — creates booking, locks availability, creates Stripe PaymentIntent, returns `booking_id` + `client_secret`.
- `POST /api/bookings/[id]/review` — buyer rating submission, triggers CIS recalculation.
- `POST /api/listings/[id]/publish` — enforces the publish guard (Stripe connected, required fields complete, ≥1 image).

</details>

---

<details>
<summary><strong>6. Buyer Portal Rules</strong></summary>

- Home/entry screen is the Live Map (`/dashboard/buyer` or `/map`), not a list view — map-first is a hard requirement, not a default that can quietly become list-first.
- Pin colours are exactly the tokens in Section 3.1 — green/orange/red/blue(selected)/purple(new) — recalculated on every filter apply, not cached stale between filter changes.
- Cluster click zooms in; it never opens a listing directly — only a single, unclustered pin opens the slide-in panel.
- Map re-query triggers on pan >25% viewport or zoom change ≥2 levels, debounced 400ms — do not requery on every pixel of drag.
- Slide-in panel opens from the right (~300px), map shifts left to accommodate — it is not a full-screen modal or a new route navigation (double-click still navigates to the full `/listings/[id]` page; single click stays in-panel).
- Filter sidebar order is fixed: Location → Radius → Asset Type → Audience → Price Range → Availability → CIS Score → Booking Type, footer Reset/Apply — do not reorder without a specific reason, buyers build muscle memory around filter position.
- Price is always displayed as £/week on cards (price_per_day × 7) with exact daily rate shown only at booking confirmation.

</details>

---

<details>
<summary><strong>7. Seller Portal Rules</strong></summary>

- Home/entry screen is the Revenue Dashboard (`/dashboard/seller`), not My Listings — revenue-first is a hard requirement matching the approved mockup.
- KPI row order is fixed: Revenue (30 days) → Active bookings → Avg CIS score → Occupancy rate.
- Main grid is 60/40 split: left = booking activity feed (scrollable), right = revenue chart (12-month bar) + CIS trend + quick actions + pending payout card. Do not invert this split or make it single-column on desktop.
- Booking status pill colours/labels must map 1:1 to the booking status enum (Section 1.3) and the exact labels seen in the approved mockup (`Live`, `Confirmed`, `Pending approval` with countdown, `Awaiting review` with sub-label) — no invented intermediate labels.
- Publish guard blocks publish if: no Stripe Connect account, missing required fields, zero images — inline red validation per field, not a single generic error banner.
- Seller cannot manually transition a booking status in the UI beyond what Section 5.2 allows (Accept/Decline on Request bookings, Upload Proof) — every other transition is system-only.

</details>

---

<details>
<summary><strong>8. Admin Portal Rules</strong></summary>

- Every admin action that mutates data (suspend account, issue refund, override CIS, adjust commission %) writes an `audit_logs` row — no silent admin mutations, ever.
- CIS override sets `is_cis_overridden = true` on the listing and displays an asterisk in the admin view — the override is visible, not hidden.
- Dispute resolution options are exactly three: Approve Seller (full payout), Full Refund, Partial Refund (custom %) — matching the booking state machine's `Disputed → Completed` / `Disputed → Refunded` transitions in Section 5.2. Do not add a fourth resolution path without updating the state machine first.
- Suspended listings are removed from all buyer queries immediately; the listing owner is not shown the suspension reason in UI (per spec) — admin-facing tools may show it, seller-facing tools must not.

</details>

---

<details>
<summary><strong>9. AI Agent Rules</strong></summary>
*(Full architecture in `marketplays_ai_agents_architecture.md` — this is the enforceable subset for build agents working on V1.1+.)*

### 9.1 Structural rule (most important rule in this entire file)

**Agents are a new client of the existing API — never a bypass of it.** A Buyer Agent or Seller Agent (or any of their sub-agents) must call the exact same endpoints in Section 5.5 that the human UI calls. No agent, sub-agent, or tool wrapper may write directly to the database or jump the booking state machine in Section 5.2.

### 9.2 Supervisor / agents-as-tools pattern

- Buyer Agent and Seller Agent are each a supervisor (PydanticAI `Agent`) holding conversation state.
- Sub-agents (Discovery, Budget & Compliance, Booking, Campaign Analytics for buyer; Listing Optimisation, Pricing, Proof & Delivery, Revenue/CIS Coach for seller) are stateless, called as tools by their supervisor, and never call each other directly or talk to the user directly.

### 9.3 Confirmation gate

- Any tool call that creates a booking, triggers a payment, publishes/unpublishes a listing, or cancels/refunds must be marked `needsApproval: true` in the Vercel AI SDK tool definition and rendered as an explicit confirm/cancel card — never auto-executed on the agent's own initiative.

### 9.4 Spend/policy limits

- Check every agent-prepared booking against `buyer_agent_policies` (max per-booking value, max monthly agent spend) before presenting it to the buyer for confirmation — this check happens in a shared policy layer used by both agents, not duplicated per sub-agent.

### 9.5 Audit

- Every side-effecting tool call approved by the policy layer writes an `audit_logs` row with `initiated_by_agent = true` and the `agent_session_id` — same table admin overrides already use (Section 4).

### 9.6 Build sequencing

- Do not build Booking, Budget & Compliance, Listing Optimisation, Pricing, Proof & Delivery, or Revenue/CIS Coach sub-agents before Discovery and Campaign Analytics are shipped and stable (V1.1 before V1.2 before V1.3 — see architecture doc Section 9). Building side-effecting agent capability before read-only capability is proven inverts the intended risk ordering.

</details>

---

<details>
<summary><strong>10. Quick Reference</strong></summary>

| Need | Where to look |
|---|---|
| Tech stack / repo conventions | Section 1 |
| Vercel + Cloudflare DNS setup | Section 2 |
| Colour tokens / component reuse | Section 3 |
| Schema constraints | Section 4 |
| Security, booking state machine, CIS formula, filters | Section 5 |
| Buyer portal fixed layout rules | Section 6 |
| Seller portal fixed layout rules | Section 7 |
| Admin audit/dispute rules | Section 8 |
| Agent safety rules (the "never bypass the API" rule) | Section 9 |

</details>

---

*Master Cursor rules file for Marketplays. Load Section 1 + 2 into every agent run; load the matching portal/domain section for the task at hand.*
