# MarketPlays — Visual Redesign Spec (Cursor Agent Reference)
> **Source:** `MarketPlays.dc.html` (design-tool reference file, proprietary templating syntax) + accompanying handoff `README.md`. Converted here into agent-readable collapsible sections.
> **This is a visual/UX spec only.** It describes what things should look like. It does not describe how to build them. See the boxed warning in Section 0 before touching anything.

---

## Table of Contents
- [0. READ FIRST — Scope of This Change](#0-read-first--scope-of-this-change)
- [1. What's New vs the Existing Build](#1-whats-new-vs-the-existing-build)
- [2. Design Tokens](#2-design-tokens)
- [3. Landing Page](#3-landing-page)
- [4. App Shell (All Logged-In Screens)](#4-app-shell-all-logged-in-screens)
- [5. Explore Map (Buyer)](#5-explore-map-buyer)
- [6. Checkout Modal](#6-checkout-modal)
- [7. My Campaigns & Spend (Buyer)](#7-my-campaigns--spend-buyer)
- [8. Revenue Dashboard (Seller)](#8-revenue-dashboard-seller)
- [9. My Listings (Seller)](#9-my-listings-seller)
- [10. Listing Editor (Modal)](#10-listing-editor-modal)
- [11. Bookings (Shared)](#11-bookings-shared)
- [12. Messages](#12-messages)
- [13. Notifications Dropdown](#13-notifications-dropdown)
- [14. Admin Panel](#14-admin-panel)
- [15. Conflicts With Earlier Design Docs](#15-conflicts-with-earlier-design-docs)
- [16. Quick Reference](#16-quick-reference)

---

<details>
<summary><strong>0. READ FIRST — Scope of This Change</strong></summary>

**This is a visual/UX update only. Do not change business logic, data models, API calls, routing behaviour, or state management to match this file.**

The existing app (already built by Cursor, running at localhost:3010) has its own component structure, state management, routing, and data layer — bookings, listings, auth, all of it. That stays exactly as it is.

`MarketPlays.dc.html` is a **design-tool export**, not production code. It uses a proprietary templating syntax (`<sc-if>`, `<sc-for>`, `{{ }}` bindings driven by a local mock-state object at the bottom of the file) purely to demonstrate the UI. **None of that templating syntax, component structure, or local mock state should be copied into the real codebase.** Its only job was to let a human preview the look.

**What to actually do, for every screen below:**
1. Recreate the **visuals** — layout, spacing, colours, typography, component styling, copy, icons — in the app's real, existing components.
2. Wire those visuals to the **existing** logic/state/props already in the app. Do not replace working logic with anything resembling the mock's local state or hardcoded sample data.
3. Where a screen or feature doesn't exist yet in the app (see Section 1), add it using the **app's existing patterns** — same state approach, same API/service layer conventions, same routing style as the rest of the codebase. Do not introduce a new pattern just because the reference file used one.

**Fidelity note:** colours, spacing, typography, and copy below are final intent — treat every hex value and pixel measurement as source of truth for *styling*. They are not a spec for *how* to fetch, store, or mutate data.

If at any point recreating a visual would require touching a data model, an API contract, or routing logic to "match the reference" — stop and treat that as a signal the reference is describing a new feature (Section 1), not a pure style change. Implement the underlying logic using the app's existing conventions first, then apply the visuals from this file on top.

</details>

---

<details>
<summary><strong>1. What's New vs the Existing Build</strong></summary>

The existing build already has: landing page, category grid, explore map with filters + detail panel, seller dashboard, my listings, bookings (accept/decline/upload proof stub).

This design adds or improves the following. Anything in this list that doesn't exist yet needs real logic added (using existing app patterns, per Section 0) — it is not purely a visual change, even though it's described visually below:

| Addition | Visual-only, or needs new logic? |
|---|---|
| Improved map view — light schematic street-map background instead of dark dot-grid, Grid view toggle | Visual-only if Grid view already has a data source; otherwise the Map/Grid toggle state is new (minimal — a view-mode flag) |
| Multi-select campaign cart — add several spaces from the map, book together in one checkout | **New logic** — cart state, multi-item checkout, needs its own data flow using existing state/service conventions |
| Checkout flow — cart review, payment method (card/invoice net-30), contract & insurance checkbox, confirmation screen | **New logic** — must call the real booking/payment endpoints already in the app, not the mock's local "confirm" handler |
| Buyer "My campaigns & spend" page — spend KPIs + campaign list | **New logic** if this aggregate view doesn't exist yet; visual spec is Section 7 |
| Ratings — 1–5 stars after "Awaiting buyer review", persists on completed bookings | Likely **partial new logic** if rating submission isn't wired yet — check existing booking review endpoint first |
| Proof-of-play upload — seller uploads photo, buyer sees it inline | README says "accept/decline/upload proof stub" already exists — likely visual-only polish plus wiring the stub to a real upload if not already done |
| Messaging — buyer↔seller thread list + conversation view | **New logic** — needs a real thread/message data source |
| Notifications centre — bell + unread badge + dropdown | **New logic** if no notification system exists yet |
| Saved searches — save/reapply/remove a filter combination | **New logic** — small, but needs persistence |
| CIS breakdown card + colour-coded CIS badges used consistently everywhere | Visual-only for the badge styling; the breakdown *factors* (verified foot traffic, on-time proofs, ratings, listing completeness) need a real data source if not already computed |
| Admin panel — platform KPIs, moderation queue, open disputes | **New logic** — needs real admin data endpoints |
| Occupancy heatmap — 30-day booked-density strip | Visual-only if occupancy-by-day data already exists; otherwise needs a small aggregation query |

**Rule of thumb:** if a feature is genuinely new, build the underlying data/state/routing exactly the way the rest of the app already does it, then style it per the relevant section below. Never let the *style* spec dictate the *architecture* of a new feature.

</details>

---

<details>
<summary><strong>2. Design Tokens</strong></summary>

### 2.1 Colours

| Token | Hex | Usage |
|---|---|---|
| App primary action | `#3B5BFF` | Buttons, active pills, links inside the app |
| Landing/marketing accent | `#2A47E8` | Wordmark, landing CTAs, landing links |
| Page background (dark/app) | `#05070C` | App shell root |
| Top bar background | `#0A0E16` | Sticky top nav |
| Card background | `#10141C` | KPI cards, list rows, panels, dropdowns |
| Input background | `#171C26` | Text inputs, selects, filter sidebar bg |
| Border (light) | `#262C38` | Card/input borders |
| Border (subtle) | `#1D2330` | Row dividers, top-bar bottom border |
| Text primary (dark theme) | `#F5F6F8` | Headings, primary values |
| Text secondary (dark theme) | `#9AA3B2` | Labels, KPI captions |
| Text tertiary (dark theme) | `#6B7280` | Meta text, timestamps, placeholders |
| Landing background gradient | `linear-gradient(180deg, #EEF1FB 0%, #E2E8FB 55%, #FFFFFF 100%)` | Landing page only |
| Landing heading | `#12141C` | Landing H1/H2 |
| Landing body | `#5B6272` | Landing paragraph text |
| Landing border | `#E4E7F1` | Category card borders, footer divider |

### 2.2 Status/semantic colours

| Status | Text | Background | Border |
|---|---|---|---|
| Green (success/available/high CIS) | `#34D399` | `#0C2A1D` | `#155336` |
| Amber (limited/mid CIS/pending) | `#F5A623` | `#2E2409` | `#5C4013` |
| Red (booked/low CIS/error) | `#F1544B` | `#301414` | `#5C1F1F` |
| Blue-info (unread/informational) | `#7AA2FF` | `#101B33` | `#233A6B` |
| Neutral/grey (no data) | `#9AA3B2` | `#171C26` | `#262C38` |

### 2.3 CIS badge thresholds (Community Impact Score — this design's name for the trust score)

- **≥ 85** → green badge
- **60–84** → amber badge
- **< 60** → red badge
- **null / no data** → grey badge, label "CIS New"

### 2.4 Map pin colours (availability)

- Available → `#22C55E`
- Limited → `#F5A623`
- Booked → `#F1544B`
- Selected pin → blue ring around the dot (uses app primary `#3B5BFF`)

### 2.5 Typography

| Use | Font | Weight | Size |
|---|---|---|---|
| Headings / wordmark | Lora (serif) | 500/600/700 | — |
| UI / body | Inter (sans) | 400–800 | — |
| Landing hero H1 | Lora | 700 | 40px / line-height 1.15 |
| Landing wordmark | Lora | 700 | 64px / line-height 1.05 |
| Section H2 (landing) | Lora | 700 | 32px |
| App page H1 | Inter | 700 | 26px |
| Card KPI value | Inter | 700 | 24px |
| Body / labels | Inter | 400–600 | 13–15px |
| Small meta text | Inter | 400 | 11.5–12.5px |

Load both families via Google Fonts (`Lora:wght@500;600;700`, `Inter:wght@400;500;600;700;800`) — match however the existing codebase already loads web fonts (next/font, etc.), don't add a second font-loading mechanism.

### 2.6 Spacing & shape

| Element | Value |
|---|---|
| Card corner radius | 14px |
| Button / input corner radius | 8–9px |
| Pill / badge / chip corner radius | 20px |
| Card padding | 18–20px |
| Page max-width (app) | 1200px |
| Page max-width (landing) | 1280px |
| Filter sidebar width | 320px |
| Listing detail panel width | 360px |

### 2.7 Shadows

| Element | Shadow |
|---|---|
| Detail panel (slides in from right) | `-12px 0 40px rgba(0,0,0,0.35)` |
| Floating cart bar | `0 16px 40px rgba(0,0,0,0.45)` |
| Dropdowns (notifications, etc.) | `0 20px 50px rgba(0,0,0,0.5)` |

</details>

---

<details>
<summary><strong>3. Landing Page</strong></summary>

- Background: gradient token from Section 2.1, full bleed.
- Top bar (1280px max-width, centred, 28px vertical / 48px horizontal padding): wordmark "MarketPlays" left (Lora 700, 22px, `#2A47E8`); right side — "Log in" text link (15px, `#454C5C`) + "Sign up" solid button (`#2A47E8` bg, white text, 10px radius, 11px/22px padding).
- Hero (max-width 720px inside the 1280px container): large serif wordmark repeated at 64px, then H1 "Book local spaces that convert" (Lora 700, 40px), then body paragraph (18px, `#5B6272`): *"Discover and reserve real-world advertising inventory — physical and digital — near the audiences you care about."*
- Three bullet lines, each with a 6px blue dot marker (`#2A47E8`) + 16px text (`#363B47`):
  1. "Discover spaces near your audience"
  2. "Book campaigns in a few clicks, or bundle several into one order"
  3. "Track presence with proof-of-play and a live Community Impact Score"
- Two CTAs side by side: "Browse as a buyer" (solid `#2A47E8`, white text) and "List as a seller" (white bg, `#2A47E8` text, 1px `#C7D0EF` border) — both 15px/26px padding, 10px radius, 16px font, weight 600.
- Category section (below hero, own 1280px container, 70px vertical padding): H2 "Spaces across every local format" (Lora 700, 32px) + subhead "Browse advertising inventory mapped to the places people already gather." (16px, `#6B7280`).
- Category grid: **5 columns, 9 cards** (Sports Club, Gym, School, Shop, Café, Festival, Community Event, Billboard, Event Venue). Each card: white bg, `#E4E7F1` border, 14px radius, 26px/18px padding, centred; 52px rounded-square icon tile (`#EAF0FF` bg) containing a simple line icon (`#2A47E8` stroke, 1.7px weight); 15px semibold label (`#22252F`) below.
- Below the grid: centred link line "Ready to book? Open the map" (16px, `#6B7280`, link in brand colour).
- Footer: 1px `#E4E7F1` top border, 26px/48px padding, flex space-between, 14px `#8A90A0` — copyright left, tagline right.

</details>

---

<details>
<summary><strong>4. App Shell (All Logged-In Screens)</strong></summary>

- Root background `#05070C` (dark theme for every logged-in screen, all roles).
- Sticky top bar, 62px tall, `#0A0E16` bg, 1px `#1D2330` bottom border, 0/28px horizontal padding.
- **Top bar left:** small logo mark (26px rounded-square, `#3B5BFF` bg, white "M" in Lora) + wordmark "MarketPlays" (white, 700, 17px), then the current role's nav tabs immediately to the right:
  - **Buyer:** Explore map · My campaigns · Bookings · Messages
  - **Seller:** Dashboard · My listings · Bookings · Messages
  - **Admin:** Admin
- **Top bar right, in order:** notification bell (36px square, `#10141C` bg, `#262C38` border, 9px radius) with an unread-count badge (red `#F1544B` circle, top-right corner, white text, 10px) that opens a dropdown (Section 13) → role switcher segmented pill group (Buyer / Seller / Admin, `#10141C` bg track with `#262C38` border, active pill `#3B5BFF`) → "Exit" text link back to the landing page (13px, `#6B7280`).
- Switching role changes both the visible nav tabs and resets to that role's default page (Buyer → Explore map, Seller → Dashboard, Admin → Admin).

</details>

---

<details>
<summary><strong>5. Explore Map (Buyer)</strong></summary>

### 5.1 Layout

Two-column grid: **320px filter sidebar** (fixed, `#0A0E16` bg, right border `#1D2330`, scrollable) + flexible map/grid area, filling the remaining viewport height below the top bar.

### 5.2 Filter sidebar — exact field order (do not reorder)

1. Heading "Filters" (17px bold white) + subhead "Refine the live map" (13px, `#6B7280`)
2. **Location** — text input
3. **Radius** — range slider, 1–10km, current value shown top-right of the label (e.g. "5 km")
4. **Asset type** — multi-select chips, wrapped flex row, active state = filled/tinted with blue outline
5. **Audience** — multi-select chips, same chip style as Asset type
6. **Price range (£/week max)** — number input
7. **Availability** — two date inputs side by side (start / end)
8. **Community Impact Score** — select: "Any score" / "85+ (excellent)" / "60+ (good)"
9. **Booking type** — select: "All types" / "Instant book" / "Request to book"
10. **Reset** (outline button) + **Save search** (solid `#3B5BFF` button) side by side
11. **Saved searches** list (only shown if any exist) — each row shows the saved label, click-to-reapply, ✕ to remove, `#10141C` bg row with `#1D2330` border

All filter inputs share the same input styling: `#171C26` bg, `#262C38` 1px border, `#F5F6F8` text, 9px radius, 14px font. Field labels are 12.5px, weight 600, `#9AA3B2`, uppercase, letter-spacing 0.04em.

**Filter logic (unchanged from existing app — do not alter):** filters are additive — AND across different filter categories (asset type AND audience AND price, etc.), OR within a multi-select category's own chips (e.g. "Gym" OR "Café" within Asset type).

### 5.3 Map area

- Background: light schematic street map, `#E7E9EE` base with a subtle grid-line pattern (`#D7DAE2`, 64px cell size) plus a few lighter rectangular block/road shapes (`#DEE1E8`) to suggest streets — **replaces the existing dark dot-grid background image/pattern only**, not the underlying map data or pin-query logic.
- Top-left overlay (floating over the map, 18px inset): a pill showing "N spaces in view" count (`#10141C` bg, white text, 20px radius) + a Map/Grid segmented toggle immediately next to it (same segmented-pill pattern as the role switcher).
- Pins: coloured dot per listing using Section 2.4 tokens; selected pin gets a blue ring; hovering/selecting shows a small price-label chip floating above the pin (`#0A0E16` bg, white text, 11px, rounded).
- Bottom-left legend explaining pin colours (available/limited/booked).
- **Grid mode** (toggle-selected): replaces the map with a card grid, `minmax(260px, 1fr)` columns, each card: photo placeholder slot, title, CIS badge, category/city line, price.

### 5.4 Listing detail panel

Fixed right-side panel, 360px wide, `#0A0E16` bg, left border, drop shadow per Section 2.7 — slides in on pin/card selection, does not navigate away from the map.

Contents top to bottom: photo placeholder slot → title + category + city → CIS badge → price (large) with a small "weekly rate" note beneath → description text → address line (with a location-pin icon) → weekly reach figure (with a people icon) → audience tags as pills → a 20-day availability strip (small coloured day-cells, same available/limited/booked palette) → **"Add to campaign cart" / "Remove from campaign cart" toggle button** (this is independent of Instant Book — cart bundles multiple spaces into one checkout, Instant Book books just this one space immediately) → sticky footer with two actions: **"⚡ Instant book"** (primary) and **"Message seller"** (secondary).

### 5.5 Campaign cart bar

Once the cart has ≥1 item, a floating pill appears fixed bottom-left: item count + running total/week + "Review & book" button, opens the checkout modal (Section 6). This is new functionality per Section 1 — needs real cart state, not just the visual pill.

</details>

---

<details>
<summary><strong>6. Checkout Modal</strong></summary>

- Centred modal, 480px wide, dark card styling (`#10141C` bg, standard card border/radius).
- Line-item list: each cart item shown with its per-item weekly price, followed by a total row.
- Payment method toggle: **Card** / **Invoice net-30** (segmented pill, same pattern as role switcher / map view toggle).
- A required checkbox: "I agree to the contract & insurance terms" — **this must be a genuine gate in the real implementation:** the "Confirm & pay £X" primary button stays disabled until checked. (The design-tool reference doesn't hard-block this — the real app must.)
- Primary button: "Confirm & pay £X" (X = computed total).
- On confirm: modal content swaps to a success state — checkmark icon, "Booking confirmed" heading, count of spaces booked, "Done" button to close.
- This entire flow needs real logic behind it (Section 1) — the confirm action must call the app's actual booking/payment creation endpoint(s), not a local mock state transition.

</details>

---

<details>
<summary><strong>7. My Campaigns & Spend (Buyer)</strong></summary>

- Page H1 "My campaigns & spend" (26px bold white) + subhead "Track everything you've booked across sellers, and where budget is going." (14px, `#6B7280`).
- 4 KPI cards in a row (`#10141C` bg, `#262C38` border, 14px radius, 20px padding): value (24px bold white) + label (13px, `#9AA3B2`) — Spend (30 days), Active campaigns, Avg cost per weekly reach, Payments due.
- "Active campaigns" section heading (16px bold white), then a list of campaign rows (same card styling as KPI cards, 18px/20px padding): campaign name + "N spaces · date range" meta line on the left; status badge + total amount on the right, flex space-between.

</details>

---

<details>
<summary><strong>8. Revenue Dashboard (Seller)</strong></summary>

- Page H1 "Revenue dashboard" + subhead "Track earnings, bookings, and Community Impact Score across your spaces."
- 4 KPI cards: Revenue (30 days) with a green delta line beneath the label, Active bookings, Avg CIS score, Occupancy rate.
- **Occupancy heatmap** card below the KPI row: heading "Occupancy — next 30 days", then a 30-column grid of small cells, 4-level green intensity scale from `#171C26` (empty) through `#123D26` → `#186B36` → `#22C55E` (fully booked).
- Two-column row below (1.4fr / 1fr split):
  - **Left — Booking activity:** list of rows, each with listing title + "buyer name · time" meta + status badge, and the amount right-aligned.
  - **Right — CIS score breakdown:** heading, then 4 labelled progress bars (verified foot traffic, on-time proof uploads, buyer ratings, listing completeness) — track `#1D2330`, fill `#3B5BFF`, label + numeric value above each bar.

</details>

---

<details>
<summary><strong>9. My Listings (Seller)</strong></summary>

- Header row: H1 "My listings" + subhead on the left, "New listing" primary button top-right (opens the listing editor modal, Section 10).
- Listing rows (card styling): title + status badge (published/draft) + CIS badge inline together on one line; category/price/image-count meta line beneath; "Edit" button (outline style) on the right.

</details>

---

<details>
<summary><strong>10. Listing Editor (Modal)</strong></summary>

- Modal heading switches between "New listing" and "Edit listing" depending on context.
- 3 photo upload slots in a row (90px tall placeholders).
- Title input (full width).
- Category select + Description textarea.
- Two-column row: Price/day + Weekly reach.
- Address input.
- Booking type toggle: **Instant book** / **Request to book** (segmented pill).
- Footer buttons: "Save as draft" (outline) and "Publish listing" (solid `#3B5BFF`) — publish should still respect whatever publish-guard validation already exists in the app (required fields, min. images, Stripe/payout connection) — this design doesn't show that guard's error states explicitly, but do not remove it.

</details>

---

<details>
<summary><strong>11. Bookings (Shared, Buyer &amp; Seller)</strong></summary>

Same page, content adapts by active role.

- Row cards: listing title, counterpart name, time, status badge, amount.
- **Seller-only:** Accept / Decline / Upload proof buttons appear on actionable bookings; once proof is uploaded, it shows inline as a photo slot on that row.
- **Buyer-only:** when a booking's status is "Awaiting buyer review", a 5-star rating prompt appears inline; once rated, the stars display permanently in place of the prompt and the status shown becomes "Completed".
- Status badge text in this design uses sentence-case display strings ("Pending payment", "Awaiting buyer review", etc.) — these are **display labels only**. Map them to whatever the existing booking status enum values already are in the app's data model; do not rename the underlying enum to match this display casing (see Section 15).

</details>

---

<details>
<summary><strong>12. Messages</strong></summary>

- Two-column layout: thread list (name, listing title, last-message preview, row highlighted when active) + conversation panel.
- Conversation panel: bubble list — right-aligned filled blue bubbles (`#3B5BFF` bg, white text) for the current user's own messages, left-aligned dark-grey bubbles (`#171C26` bg, `#C7CCD6` text) for the other party. Bubble radius 12px, 10px/14px padding, max-width 70%.
- Text input + Send button fixed at the bottom of the conversation panel.
- This is new functionality (Section 1) — needs a real thread/message data source wired in using the app's existing service-layer conventions.

</details>

---

<details>
<summary><strong>13. Notifications Dropdown</strong></summary>

- Anchored under the bell icon, 320px wide, `#10141C` bg, `#262C38` border, 12px radius, drop shadow per Section 2.7, small fade-in on open.
- "Notifications" label header (13px, `#9AA3B2`).
- Row list: unread rows tinted `#101B33`, each row shows message text (13px, `#F5F6F8`) + relative time (11.5px, `#6B7280`).
- **Opening the dropdown marks all notifications read** (badge clears) — confirm this is the desired real behaviour before wiring it exactly this way; it's a plausible UX choice but a product decision, not just a style choice.

</details>

---

<details>
<summary><strong>14. Admin Panel</strong></summary>

- 4 KPI cards: GMV (30 days), Active listings, Pending moderation, Open disputes.
- **Listing moderation queue:** rows with title, seller, category, submitted date, and Approve/Reject buttons — approving or rejecting removes the row from the queue.
- **Open disputes:** rows with booking reference, issue description, status badge.
- This is new functionality (Section 1) — needs real admin data endpoints; the visual spec above applies once that data exists.

</details>

---

<details>
<summary><strong>15. Conflicts With Earlier Design Docs</strong></summary>

This file **supersedes** the design tokens in `marketplays_cursor_build_guide.md` Section 2 and `marketplays_cursor_rules.md` Section 3 for anything visual — this is the newer, higher-fidelity reference and Cursor has already built against it. Specifically:

| Item | Earlier doc said | This doc says | Which wins |
|---|---|---|---|
| Primary brand colour | `#1A56DB` | App: `#3B5BFF` · Landing: `#2A47E8` | **This doc** |
| Trust-score name | "CIS" / "Campaign Integrity Score" | "CIS" / "Community Impact Score" | **This doc** — same acronym, name has evolved; keep using "CIS" in code/variable names, update user-facing copy to "Community Impact Score" |
| CIS colour thresholds | 90/80/70/60 bands (5 tiers) | 85 / 60 (3 tiers: green ≥85, amber 60–84, red <60, grey null) | **This doc** |
| Booking status display text | `Pending_Payment`, `Awaiting_Buyer_Review`, etc. (enum-cased) | "Pending payment", "Awaiting buyer review" (sentence case) | **This doc, for display only** — do not rename the actual backend enum values (`marketplays_cursor_rules.md` Section 1.3 / 5.2 stay authoritative for the enum itself); this is a presentation-layer label mapping |
| Landing page background | Not previously specified as gradient | Light gradient `#EEF1FB → #E2E8FB → #FFFFFF` | **This doc** |

Nothing here changes the API contracts, database schema, or booking state machine transitions defined in `Marketplays_Developer_Specification.docx` and `marketplays_cursor_rules.md` Sections 4–5 — those remain authoritative. Only the visual layer changed.

</details>

---

<details>
<summary><strong>16. Quick Reference</strong></summary>

| Need | Where to look |
|---|---|
| The one rule that matters most | Section 0 |
| What's genuinely new vs just restyled | Section 1 |
| Colours, fonts, spacing, shadows | Section 2 |
| Landing page copy/layout | Section 3 |
| Shared app shell (nav, role switcher, bell) | Section 4 |
| Explore map — filter order, panel spec, cart | Section 5 |
| Checkout modal | Section 6 |
| Buyer campaigns page | Section 7 |
| Seller revenue dashboard | Section 8 |
| My listings / listing editor | Sections 9–10 |
| Bookings (shared) | Section 11 |
| Messages / Notifications | Sections 12–13 |
| Admin panel | Section 14 |
| What changed vs older design docs | Section 15 |

</details>

---

*Visual redesign reference for MarketPlays, converted from `MarketPlays.dc.html` + handoff `README.md`. Style only — existing business logic, data models, and API contracts are unchanged. Pair with `marketplays_cursor_rules.md` for anything non-visual.*
