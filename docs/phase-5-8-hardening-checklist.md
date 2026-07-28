# Phases 5-8 — Hardening Checklist

> **Compatibility / audit only.** Source: `docs/marketplays_launch_roadmap.md` Phases 5-8.
> Do **not** treat this file as a build order ahead of Phase 1 journeys. Phases 5-8 are cross-cutting hardening passes — run them continuously once journeys work, not as gold-plate blockers.
> Companion: [`docs/launch-ready-definition.md`](./launch-ready-definition.md) · Phase 1 gaps: [`docs/phase-1-mvp-gap-checklist.md`](./phase-1-mvp-gap-checklist.md) (when present).

**Status legend:** Done · Partial · Missing · N/A (legal/human)

---

## Phase 5 — Performance

**Target (roadmap):** page loads **under 2 seconds** on a typical connection; aligns with map initial load **<2s** and API search **<300ms p95** (`docs/filter-logic.md`).

### Checklist — current state + gaps

| Area | Status | Current state | Gap / next verify |
|------|--------|---------------|-------------------|
| **Image loading** | Missing | No `next/image` usage found under `apps/web/src`. Listing images are URL strings / empty mock arrays (`mock-listings.ts`). No CDN image pipeline or responsive `sizes`/`srcset`. | Adopt `next/image` (or equivalent) for listing/marketing media; define Storage/CDN URLs; measure LCP on listing + map. |
| **Map performance** | Partial | Mapbox GL is **dynamically imported** in `apps/web/src/hooks/useMap.ts` with GeoJSON **clustering**. Root `layout.tsx` still eagerly imports Mapbox CSS globally. Buyer map often fed by mocks, not live dense data. | Confirm pan/zoom refetch debounce (>=400ms / 25% viewport rules per research docs) against live API; avoid loading Mapbox CSS on non-map routes; stress-test pin volume caps. |
| **Database queries** | Missing / Partial | Listing search still uses **in-memory store** (`apps/api/app/services/listing_service.py` + `memory_store`). SQLAlchemy models exist but PostGIS GiST / `ST_DWithin` / bbox indexes are **not** wired for production search. Target <300ms p95 is documented, not measured. | Replace memory search with PostGIS + indexes (`docs/research-recommendations.md`); `EXPLAIN ANALYZE` under realistic volume; keep list cap <=20, separate pin endpoint cap. |
| **Caching (Cloudflare)** | N/A under current hosting | Hosting is **Vercel + Cloudflare DNS-only (grey cloud)** — see below. No Cloudflare edge cache/WAF while DNS-only. | Optimise via **Vercel** CDN/caching headers and asset optimisation. Do **not** orange-cloud proxy app traffic to "get Cloudflare caching." |
| **Lazy loading** | Partial | Mapbox JS is code-split via dynamic `import()`. No systematic route-level `dynamic()` / image lazy-load / below-fold deferral audit. | Lazy-load heavy portal chunks (charts, map, day-picker) off critical path; lazy images. |
| **Mobile responsiveness** | Partial | Tailwind responsive breakpoints used on marketing and some admin/buyer surfaces. Map + slide-in panel need real-device QA (touch, viewport height, filter drawer). | Phase 8 device pass; fix layout regressions before launch polish. |
| **<2s page-load target** | Missing (unverified) | No Lighthouse/Web Vitals gate in CI; no recorded baseline against production-like data. | Measure `/`, `/map`, listing detail, seller dashboard on mid-tier mobile + desktop; fix regressions that break <2s. |

### Cloudflare CDN vs DNS-only (do not conflate)

| Concept | Decision |
|---------|----------|
| **DNS-only (grey cloud)** | **Required** for apex/`www`/`api` -> Vercel. Proxying breaks Vercel SSL. Authoritative: `docs/marketplays_cursor_rules.md` section 2.4, `docs/deployment.md`. |
| **Cloudflare CDN / proxy cache** | **Out of scope under current hosting.** Requires Proxied mode — off-limits. |
| **Phase 5 "Caching (Cloudflare)" in roadmap** | Means edge/CDN behaviour in principle; under Marketplays hosting, satisfy performance via **Vercel** static/asset caching — **not** by enabling Cloudflare proxy. |

---

## Phase 6 — Security

Most technical rules are already in `docs/marketplays_cursor_rules.md` section 5.1. This phase **confirms implementation**, not redesign. Auth provider for launch is **Clerk** (roadmap Conflicts — supersedes JWT/bcrypt for auth identity).

| Item | Status | Current state | Gap |
|------|--------|---------------|-----|
| **Clerk auth rules** | Missing (cutover) | API still uses **custom JWT + bcrypt** (`apps/api/app/middleware/auth.py`, `auth_service`, login rate tests). `@clerk` **not** in `apps/web/package.json`. Roadmap mandates Clerk; rules 5.1 JWT bullets are superseded for IdP only. | Finish Clerk migration plan (Compatibility Agent 2); keep **server-side RBAC** (buyer/seller/admin) on every protected route after Clerk session/claims replace JWT. |
| **Supabase RLS** | Missing | No SQL migrations / `CREATE POLICY` / RLS enablement found in repo. API commonly uses service role / memory store patterns. | Define and apply RLS for user-scoped tables; never rely on client anon key alone; document service-role server-only usage. |
| **Stripe webhook validation** | Done (code + tests) | `Stripe-Signature` validated; invalid -> HTTP 400 (`apps/api/app/services/stripe_service.py`, `apps/api/app/api/payments.py`, `tests/test_stripe_webhook.py`). | Re-verify on preview **and** production webhook secrets; never skip signature check. |
| **Input validation** | Partial | Pydantic schemas on several routes (e.g. admin/listings). Not every endpoint audited; memory-store paths may skip DB constraints. | Systematic schema coverage; reject unknown fields; money as integer pence only. |
| **Rate limiting** | Partial | In-memory limits: login **5/IP/15min**, authenticated **100/min** (`apps/api/app/middleware/rate_limit.py`). Fine for single-instance MVP; **not** shared across Vercel isolates. | Confirm behaviour under multi-instance; consider durable limiter before abuse-scale launch. |
| **Image validation** | Missing | Section 5.1 requires MIME (not extension), max size server-side, malware scan before serving. `mime_type` column on deliverables exists; **no** upload MIME/size/malware enforcement found. Malware scan must **not** run in a Vercel Function (rules 2.3 — worker/queue). | Implement upload validation + async scan path before public serve. |
| **GDPR compliance** | **Legal / human** | Not an agent coding task. Needs DPIA/process, retention, DSAR/deletion path, lawful basis — human + counsel. | Flag to human/legal. Agents may scaffold *technical* hooks (export/delete endpoints) only when instructed; **do not** invent compliance claims. |
| **Privacy policy** | **Legal / human** | No in-product Privacy page found. | **Human/legal drafts binding copy.** Do not ship agent-authored Privacy as binding. |
| **Terms of service** | **Legal / human** | No in-product ToS page found. | **Human/legal drafts binding copy.** Do not ship agent-authored ToS as binding. |

### Legal flag (explicit)

> **GDPR, Privacy Policy, and Terms of Service require human/legal ownership.** Agents must not draft unsupervised binding legal text. Engineering may add empty routes/footer links and wire consent UI **after** counsel-approved copy is provided.

---

## Phase 7 — Analytics

### Product / usage analytics (this phase) vs in-app dashboards

| Kind | What it is | Examples in Marketplays |
|------|------------|-------------------------|
| **Phase 7 — external tooling** | Platform health, funnel, errors for the **business** | GA4, PostHog, Sentry |
| **In-app dashboards** | User-facing portal features (already specified) | Seller revenue/CIS charts (`RevenueChart` / recharts), buyer campaign spend, admin GMV stubs |

**Do not conflate.** Shipping seller "Analytics" UI is not the same as installing GA4/PostHog/Sentry.

### Install status

| Tool | Status | Evidence |
|------|--------|----------|
| **Google Analytics 4** | Missing | No `gtag` / GA4 package / env wiring in `apps/web`. |
| **PostHog** | Missing | No `posthog` dependency or client init. |
| **Sentry** (or equivalent) | Missing | No `@sentry/*` in web/api dependencies. |

### Events to track (when installing — not in this compatibility pass)

- Sign-ups
- Listings created
- Bookings
- Payments
- Drop-off points
- Conversion rates

**This checklist does not implement GA4/PostHog/Sentry.** Install only after Phase 1 journeys are reliable; avoid gold-plating analytics before launch-ready journeys work.

---

## Phase 8 — QA Testing

**Gate:** Fix every issue found before launch. These scripts are the literal "Definition of Launch Ready" acceptance runs — manual or automated E2E, not a design review.

**How to use:** Time the seller publish path (<10 min bar from Phase 1.2). Record environment (Preview/Production, Stripe test/live). Mark Pass/Fail; file bugs for every Fail.

### Seller journey — executable checklist

| # | Step | Pass | Fail | Notes |
|---|------|:----:|:----:|-------|
| S1 | Register (Clerk / agreed auth) | [ ] | [ ] | |
| S2 | Create / complete profile | [ ] | [ ] | |
| S3 | Connect Stripe Connect | [ ] | [ ] | |
| S4 | Publish listing (images, pricing, availability; publish guard) | [ ] | [ ] | Target: first live listing <10 minutes end-to-end |
| S5 | Receive booking (Instant or Request per listing type) | [ ] | [ ] | |
| S6 | Receive payout (after campaign complete / release path) | [ ] | [ ] | |

**Seller run metadata**

| Field | Value |
|-------|-------|
| Date | |
| Tester | |
| Environment | |
| Build / commit | |
| Timed publish (minutes) | |
| Overall seller journey | Pass [ ] / Fail [ ] |


### Buyer journey — executable checklist

| # | Step | Pass | Fail | Notes |
|---|------|:----:|:----:|-------|
| B1 | Register | [ ] | [ ] | |
| B2 | Browse map | [ ] | [ ] | |
| B3 | Filter listings | [ ] | [ ] | AND across types, OR within multi-select |
| B4 | Book listing | [ ] | [ ] | |
| B5 | Pay (Stripe) | [ ] | [ ] | |
| B6 | Leave review | [ ] | [ ] | |

**Buyer run metadata**

| Field | Value |
|-------|-------|
| Date | |
| Tester | |
| Environment | |
| Build / commit | |
| Overall buyer journey | Pass [ ] / Fail [ ] |


### Launch-ready journeys (extended buyer tracking)

Roadmap "Definition of Launch Ready" also requires buyer **track the campaign** between pay and review. Use during full acceptance:

| # | Step | Pass | Fail | Notes |
|---|------|:----:|:----:|-------|
| B4a | Booking confirmation visible | [ ] | [ ] | |
| B4b | Track campaign / booking history through statuses | [ ] | [ ] | |
| B6 | Leave review (same as B6 above) | [ ] | [ ] | |


---

## Sequencing reminder

1. Prove Phase 1 / Definition of Launch Ready journeys first — see [`docs/launch-ready-definition.md`](./launch-ready-definition.md).
2. Harden with Phases 5-8 continuously; do not block launch on analytics depth or performance headroom beyond the <2s bar.
3. Nice-to-Have and AI agent layer stay **out of scope** until after launch-ready journeys.
