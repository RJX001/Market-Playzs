# Phase 1 MVP Gap Checklist

> **Audit only** (Compatibility Agent 3). Surveyed against `docs/marketplays_launch_roadmap.md` Phase 1 (1.1–1.4) + Definition of Launch Ready.  
> **Date:** 2026-07-28 · **Repo:** Market-Plays  
> **No product code was changed.**

### Status legend

| Status | Meaning |
|--------|---------|
| **Done** | Present in UI and wired to a working API path end-to-end |
| **Partial** | UI and/or API exists, but not a complete working journey (stub, mock data, or one side only) |
| **Missing** | No meaningful implementation for this requirement |

### Cross-cutting finding

The FastAPI app (`apps/api`) has substantial in-memory / service-layer logic for auth (JWT+bcrypt), listings, bookings, payments, availability, and CIS. The Next.js app (`apps/web`) is largely **UI on mock/stub data** and does **not** call those endpoints for buyer/seller journeys. There is no Clerk SDK. `@stripe/stripe-js` is in `apps/web/package.json` but unused (no `loadStripe` / Elements).

---

## 1.1 Authentication

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Clerk authentication | **Missing** | No `@clerk/*` in `apps/web/package.json`. Zero Clerk imports / `clerkMiddleware` under `apps/web` or `apps/api`. Roadmap Conflicts claim (“Clerk is what's actually implemented”) is **incorrect** vs codebase. Auth is custom JWT+bcrypt: `apps/api/app/api/auth.py`, `apps/api/app/services/auth_service.py`. |
| Google sign-in | **Missing** | No OAuth/Google identity routes or buttons. Login/register are email+password forms only (`apps/web/src/app/auth/login/page.tsx`, `auth/register/page.tsx`). `next/font/google` in `layout.tsx` is fonts, not auth. |
| Email sign-in | **Partial** | **API Done:** `POST /api/auth/register`, `/login`, `/refresh`, `/logout` — `apps/api/app/api/auth.py` + `auth_service.py` (bcrypt cost 12, JWT 15m / refresh 7d), tests in `apps/api/tests/test_auth.py`. **Frontend stub:** forms have no `onSubmit` / `fetch` — `apps/web/src/app/auth/login/page.tsx`, `register/page.tsx`, `register/seller/page.tsx`. |
| User profiles | **Partial** | **Model only:** `apps/api/app/models/user.py` (`full_name`, `company_name`, `phone`, role, Stripe fields). Nested in auth responses (`apps/api/app/schemas/auth.py`). **Missing:** profile CRUD endpoints; no seller/buyer profile or settings pages under `apps/web`. |
| Buyer/Seller role selection at signup | **Partial** | **API:** `RegisterRequest.role: buyer \| seller` — `apps/api/app/schemas/auth.py`. **UI stub:** separate pages with hidden role fields — `apps/web/src/app/auth/register/page.tsx` (buyer), `register/seller/page.tsx` (seller). Forms never POST to API. Single role on user row (no dual-role model). |
| Role switching (header pill) | **Partial** | **UI Done as chrome:** `apps/web/src/components/shared/RoleToggle.tsx` linked from `PortalHeader.tsx` (buyer/seller/admin shells). Navigates portal homes only. **No auth/session logic:** no role claim update, no gate that user may switch, portals reachable by URL without session. |

**1.1 summary:** 2 Missing · 4 Partial · 0 Done

---

## 1.2 Seller onboarding

Success bar (roadmap): *new seller creates a live listing in &lt;10 minutes* — **not achievable in-product today** (UI stubs + no image upload + no Connect UI + register unwired).

| Step | Status | Evidence |
|------|--------|----------|
| 1. Complete profile | **Partial** | Seller register stub: `apps/web/src/app/auth/register/seller/page.tsx` (name, business, email, password — no submit). API register accepts seller fields: `apps/api/app/api/auth.py`. No post-signup profile completion page under `apps/web/src/app/(seller)/`. |
| 2. Connect Stripe Connect | **Partial** | **API:** `POST /api/payments/connect/account-link` — `apps/api/app/api/payments.py` → `stripe_service.create_connect_account_link`. **UI Missing:** checklist copy only in `apps/web/src/components/seller/PublishGuard.tsx`; `ListingWizard` takes static `stripeConnected` prop; no Connect CTA / return pages; `SELLER_NAV` has no payouts item (`apps/web/src/lib/constants.ts`). |
| 3. Create first listing | **Partial** | **UI stub:** `apps/web/src/app/(seller)/listings/new/page.tsx` → `ListingWizard.tsx`; list/edit use `SELLER_LISTINGS` from `stub-data.ts`. Save/Publish have no API handlers. **API:** `POST /api/listings` — `apps/api/app/api/listings.py` → `listing_service.create_listing_draft`. |
| 4. Upload images | **Missing** | Wizard photo slots are non-functional buttons (`ListingWizard.tsx`). No upload/presign/storage route under `apps/api`. Schemas accept `images: list[str]` URLs only (`apps/api/app/schemas/listings.py`). Publish guard expects non-empty images but there is no way to upload them. |
| 5. Set pricing | **Partial** | Local-state `pricePerDayPence` in `ListingWizard.tsx`. API accepts `price_per_day_pence` on create/update; publish rejects missing/negative. Not wired to API. |
| 6. Set availability | **Partial** | **API:** `GET/POST /api/availability/{listing_id}` — `apps/api/app/api/availability.py`. **UI Missing:** no availability editor in seller wizard, listings, or dashboard. Publish does **not** require availability windows. |
| 7. Publish listing (+ guards) | **Partial** | **UI stub:** `PublishGuard.tsx` + `canPublish` disable in `ListingWizard.tsx` (no `fetch`). Edit page incorrectly proxies Stripe via `status === "published"` (`listings/edit/[id]/page.tsx`). **API Done (memory):** `POST /api/listings/{id}/publish` → `listing_service.publish_listing` guards Stripe (`stripe_account_id` + `stripe_charges_enabled`), required fields, ≥1 image. |

**1.2 summary:** 1 Missing · 6 Partial · 0 Done

---

## 1.3 Buyer journey

| Step | Status | Evidence |
|------|--------|----------|
| 1. Browse map | **Partial (UI stub, no API wire)** | `apps/web/src/app/(buyer)/map/page.tsx` → `buyer-map-page-client.tsx`. Pins from `MOCK_BUYER_LISTINGS` (`mock-listings.ts`), not `GET /api/listings`. Mapbox via `useMap.ts` when token set. |
| 2. Search | **Partial (UI stub, no API wire)** | Location + radius inputs in `filter-sidebar.tsx`. Client `filter-listings.ts` does **not** apply location/radius. Backend search (bbox/radius) in `apps/api/app/api/listings.py` + `listing_service.py` unused by web. |
| 3. Filters | **Partial (UI stub, no API wire)** | Full sidebar UI: asset type, audience, price, dates, CIS, booking type (`filter-sidebar.tsx`). Client filters mocks only; availability date range not applied in `filter-listings.ts`. API query params exist, unused. |
| 4. View listing | **Partial (UI stub, no API wire)** | Slide-in: `listing-slide-in-panel.tsx`. Detail: `apps/web/src/app/listings/[id]/page.tsx` via `getMockListingById` — not `GET /api/listings/{id}`. |
| 5. Book listing | **Partial (soft-fail / draft UX)** | `useBooking.ts` `POST`s `/api/bookings` on the **Next** origin (no `apps/web/src/app/api/**` proxy). 404/network → treated as success draft. Real create: `apps/api/app/api/bookings.py` + `booking_service.py`. Slide-in always “Instant book”; Request path not branched. |
| 6. Pay with Stripe | **Partial (backend only; no buyer Stripe UI)** | Checkout Card/Invoice toggle: buyer checkout modal. `@stripe/stripe-js` installed but **no** Elements / `confirmPayment`. API creates PaymentIntent in `stripe_service.py`; webhook in `payments.py`. Client ignores `client_secret`. |
| 7. Booking confirmation | **Partial (UI stub, no API wire)** | Success copy in checkout modal after soft-success draft. No webhook→`Confirmed` UI path. Instant book from map panel has no dedicated confirmation screen. |
| 8. Booking history | **Missing** | Buyer nav “Bookings” → `/bookings` (`constants.ts`) but only seller page exists: `apps/web/src/app/(seller)/bookings/page.tsx` (mock feed). Campaigns list is mock: `campaigns-page-client.tsx`. API has `GET /api/bookings/{id}` only — **no list-my-bookings**. |

**1.3 summary:** 1 Missing · 7 Partial · 0 Done

---

## 1.4 Listing pages

Public detail: `apps/web/src/app/listings/[id]/page.tsx` · Map panel: `listing-slide-in-panel.tsx` · API detail unused: `GET /api/listings/{id}`.

| Feature | Status | Evidence |
|---------|--------|----------|
| Images | **Partial (UI stub, empty)** | Placeholder aspect-ratio blocks; mocks have empty `imageUrls` (`mock-listings.ts`). No gallery render of real URLs. |
| Description | **Partial (mock text only)** | Rendered from mock on detail + slide-in. Not fetched from API. |
| Audience | **Partial (mock tags/reach)** | Tags + weekly reach on detail/panel. API `audience_tags` unused by page. |
| Price | **Partial (mock pence → £ UI)** | `formatWeeklyPriceFromDailyPence` / `penceToPoundsDisplay` — correct pence convention, mock source. |
| Availability calendar | **Missing** | `components/ui/calendar.tsx` exists unused. Slide-in uses a deterministic 20-day colour strip (“until occupancy API”). Detail shows text availability only. `apps/api/app/api/availability.py` unused by web. |
| CIS score | **Partial (mock badge; API unused)** | `CISBadge` on detail + panel from mock score. API: `apps/api/app/api/cis.py` + `cis_service.py` unused by listing page. |
| Reviews | **Missing** | No reviews section on listing UI. Submit API only: `POST /api/bookings/{id}/review` (`bookings.py`); model `apps/api/app/models/review.py`. |
| Instant Book / Request Booking | **Partial (label stub)** | Detail CTA text switches Instant vs Request but both link to `/map`. Slide-in always Instant book. No Request accept/decline buyer flow; seller accept/decline disabled on stub bookings page. |

**1.4 summary:** 2 Missing · 6 Partial · 0 Done

---

## Launch Ready journeys

Maps Definition of Launch Ready (roadmap) to current status. These are the literal E2E acceptance journeys.

### Seller (1–6)

| # | Journey step | Status | Evidence / gap |
|---|--------------|--------|----------------|
| 1 | Sign up | **Partial (UI stub, no API wire)** | Forms: `auth/register/seller/page.tsx`, `auth/login/page.tsx`. API: `apps/api/app/api/auth.py`. |
| 2 | Create a profile | **Missing** | No seller profile/settings route or completion flow under `apps/web`. Register collects fields but does not persist via API. |
| 3 | Connect Stripe | **Partial (API exists; no seller UI)** | `POST /api/payments/connect/account-link`. UI checklist only (`PublishGuard.tsx`). |
| 4 | Publish a listing | **Partial (UI stub, no API wire)** | Wizard + publish guards UI; no handlers. API publish + guards in `listing_service.py`. Image upload **Missing** blocks real publish. |
| 5 | Receive a booking | **Partial (backend + seller UI stub)** | Create/lock/PI: `booking_service.py`. Seller bookings page mock + disabled actions: `(seller)/bookings/page.tsx`. |
| 6 | Get paid | **Partial (backend transfer; UI unused)** | `transfer_on_completed` in `stripe_service.py` on Completed. `PendingPayoutCard.tsx` exists but not mounted on seller dashboard (`dashboard/page.tsx` uses stubs). |

### Buyer (1–7)

| # | Journey step | Status | Evidence / gap |
|---|--------------|--------|----------------|
| 1 | Sign up | **Partial (UI stub, no API wire)** | `auth/register/page.tsx` vs `auth.py`. |
| 2 | Search the map | **Partial (UI stub, no API wire)** | Map + search UI on mocks; API search unused. |
| 3 | Filter results | **Partial (client mock filters)** | `filter-sidebar.tsx` + `filter-listings.ts` on `MOCK_BUYER_LISTINGS`. |
| 4 | Book | **Partial (soft-success drafts)** | `useBooking.ts` soft-fails to local draft when Next `/api/bookings` 404s. |
| 5 | Pay | **Partial (no Stripe Elements)** | Checkout UI without PaymentIntent confirm; Stripe SDK unused. |
| 6 | Track the campaign | **Partial (UI stub, no API wire)** | `/campaigns` mock KPIs (`campaigns-page-client.tsx`); `/campaigns/[id]` explicit stub (“will connect here”). |
| 7 | Leave a review | **Missing (API only)** | `POST /api/bookings/{id}/review` + `submit_review` in `booking_service.py`. No buyer review UI. |

**Launch Ready summary:** 2 Missing · 11 Partial · 0 Done · **0 fully working E2E journeys**

---

## Missing items count

| Section | Missing rows |
|---------|--------------|
| 1.1 Auth | 2 (Clerk, Google) |
| 1.2 Seller onboarding | 1 (Upload images) |
| 1.3 Buyer journey | 1 (Booking history) |
| 1.4 Listing pages | 2 (Availability calendar, Reviews) |
| Launch Ready (unique rows marked Missing) | 2 (Create profile, Leave review) |
| **Total Missing** | **8** |

> Note: “Leave a review” (Launch Ready) overlaps “Reviews” (1.4). Counted as separate checklist rows per mandate tables. If deduped by capability, unique Missing capabilities ≈ **7**.

---

## Highest-leverage gaps (for sequencing, not implementation)

1. Wire `apps/web` → FastAPI (base URL / proxy + auth cookies/Bearer) — almost every Partial is blocked here.  
2. Replace mock/stub data (`mock-listings.ts`, `seller/stub-data.ts`) with live listing/booking APIs.  
3. Image upload path (storage + wizard) — required by publish guard.  
4. Stripe Connect UI for sellers + Elements/`client_secret` for buyers.  
5. Buyer bookings/history + review UI; listing availability calendar.

---

*Generated from codebase survey. Pair with `docs/marketplays_launch_roadmap.md` for priority and `docs/marketplays_cursor_rules.md` for mechanics.*
