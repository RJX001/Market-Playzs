# Marketplays — Launch-Readiness Roadmap
> **Agent-readable reference.** This is a **stabilise-and-ship** roadmap, not a new-feature spec. Cursor has already built the core platform — this file sequences what's left to make it stable, usable, and launch-ready, in priority order.
> Companion docs: `marketplays_cursor_rules.md` (rules/enums/state machine — still authoritative for *how* things work), `marketplays_visual_redesign_spec.md` (visual layer), `marketplays_ai_agents_architecture.md` (post-launch, not part of this roadmap).

---

## Table of Contents
- [0. Mandate — Read Before Assigning Any Work](#0-mandate--read-before-assigning-any-work)
- [Phase 1 — Complete the MVP (Highest Priority)](#phase-1--complete-the-mvp-highest-priority)
- [Phase 2 — Admin Dashboard](#phase-2--admin-dashboard)
- [Phase 3 — Payments](#phase-3--payments)
- [Phase 4 — Notifications](#phase-4--notifications)
- [Phase 5 — Performance](#phase-5--performance)
- [Phase 6 — Security](#phase-6--security)
- [Phase 7 — Analytics](#phase-7--analytics)
- [Phase 8 — QA Testing](#phase-8--qa-testing)
- [Nice-to-Have (After Launch)](#nice-to-have-after-launch)
- [Definition of "Launch Ready"](#definition-of-launch-ready)
- [Conflicts / Notes vs Earlier Docs](#conflicts--notes-vs-earlier-docs)
- [Quick Reference](#quick-reference)

---

<details>
<summary><strong>0. Mandate — Read Before Assigning Any Work</strong></summary>

**At this stage, the job is not to add new features. The priority is stability, usability, and launch-readiness.**

Rules for every Cursor agent and sub-agent working from this file:

- Do not propose or add scope beyond what's listed here. If a phase looks incomplete without an obvious extra feature, flag it to the human rather than building it silently.
- Work the phases roughly in order — Phase 1 (MVP completion) blocks everything else being meaningful. Phases 2–4 can parallelise across branches once Phase 1's two end-to-end journeys (Section "Definition of Launch Ready") work reliably. Phases 5–8 are cross-cutting hardening passes that apply to whatever's been built so far, not separate features — run them continuously, not only at the end.
- Every item below assumes the existing rules in `marketplays_cursor_rules.md` still apply (booking state machine, CIS formula, security baseline, DB schema). This file governs *sequencing and priority*, not the underlying mechanics — don't re-derive those, reference the rules file.
- The **AI agent layer** (`marketplays_ai_agents_architecture.md`) and anything under "Nice-to-Have" below are explicitly **out of scope** until after the two end-to-end journeys are launch-ready. Do not let an agent get pulled into building the Buyer/Seller Agent while Phase 1 is still incomplete.

</details>

---

<details>
<summary><strong>Phase 1 — Complete the MVP (Highest Priority)</strong></summary>

### 1.1 Authentication

- Finish **Clerk** authentication (see [Conflicts section](#conflicts--notes-vs-earlier-docs) — this supersedes the original custom JWT/bcrypt auth plan in the developer spec).
- Google sign-in.
- Email sign-in (optional — don't block launch on this if Google sign-in is solid).
- User profiles.
- Buyer/Seller role selection at signup.
- Role switching (the header pill toggle already specified in the visual redesign spec, Section 4 — this is the UI; the auth/session logic behind it is what Phase 1 covers).

### 1.2 Seller Onboarding

Build the complete flow, in this order:

1. Complete profile
2. Connect Stripe Connect
3. Create first listing
4. Upload images
5. Set pricing
6. Set availability
7. Publish listing

**Success bar: a new seller can create a live listing in under 10 minutes.** Treat this as a testable acceptance criterion, not a vague aspiration — time an actual run-through during QA (Phase 8).

The publish-guard rule already specified (`marketplays_cursor_rules.md` Section 5.5 / 7) still applies: block publish if Stripe isn't connected, required fields are missing, or there are zero images.

### 1.3 Buyer Journey

Complete, end to end:

1. Browse map
2. Search
3. Filters
4. View listing
5. Book listing
6. Pay with Stripe
7. Booking confirmation
8. Booking history

This is the buyer half of the same acceptance bar as Section 1.2 — it needs to work reliably, not just exist. Map/filter behaviour, pin states, and the slide-in panel are already fully specified in `marketplays_cursor_build_guide.md` Section 4 and `marketplays_visual_redesign_spec.md` Section 5 — this phase is about wiring those existing visuals to working data, not redesigning them.

### 1.4 Listing Pages

Each listing page needs all of the following present and working:

- Images
- Description
- Audience
- Price
- Availability calendar
- CIS score
- Reviews
- Instant Book / Request Booking

Booking-type behaviour (Instant vs Request) follows the state machine already defined in `marketplays_cursor_rules.md` Section 5.2 — no new statuses, no shortcuts around the 24hr accept/decline window for Request bookings.

</details>

---

<details>
<summary><strong>Phase 2 — Admin Dashboard</strong></summary>

### 2.1 Manage Users
- Approve sellers
- Suspend users
- Edit listings
- Verify businesses

### 2.2 Manage Listings
- Edit
- Approve
- Reject
- Feature listings

### 2.3 Bookings
- View all bookings
- Booking status
- Refunds
- Disputes

Dispute resolution options stay exactly the three already defined (`marketplays_cursor_rules.md` Section 8): Approve Seller, Full Refund, Partial Refund — don't add a fourth path here without updating the state machine first.

### 2.4 Analytics (admin-facing)

Dashboard showing:
- Users
- Sellers
- Buyers
- Listings
- Bookings
- GMV
- Revenue
- Commission earned

This is the internal admin view of the same GMV/revenue/commission figures modelled in `marketplays_revenue_model.html` — reuse the same definitions (GMV = booking value before commission; revenue = commission + featured + subscriptions) so the admin dashboard and the revenue model never disagree on what a number means.

Every admin action in this phase (suspend, approve/reject listing, refund, feature) must write an `audit_logs` row per the existing rule — no silent admin mutations.

</details>

---

<details>
<summary><strong>Phase 3 — Payments</strong></summary>

Finish Stripe Connect. Flow (already specified in full in `marketplays_cursor_rules.md` Section 5.2 — this phase is "finish implementing it," not "design it"):

```
Buyer pays → Platform holds payment (escrow) → Seller completes campaign
→ Buyer confirms → Payment released automatically
```

Also needed:
- Refunds (per the cancellation/refund table already defined in the developer spec)
- Failed payments handling
- Payout history (seller-facing — ties into the "Pending payout" card already specified in the seller dashboard visual spec)

Webhook signature validation (`Stripe-Signature` header, reject unsigned with 400) is non-negotiable per the security rules already defined — verify this is actually enforced, don't just assume it from the original spec.

</details>

---

<details>
<summary><strong>Phase 4 — Notifications</strong></summary>

Email + in-app, both required (in-app bell/dropdown UI already specified in `marketplays_visual_redesign_spec.md` Section 13).

**Seller notifications:**
- New booking
- Booking cancelled
- Payment released
- Review received

**Buyer notifications:**
- Booking confirmed
- Campaign live
- Campaign complete
- Review reminder

Opening the in-app notification dropdown marks all read (per the visual spec) — confirm this is still the desired behaviour for the real build before wiring it exactly that way.

</details>

---

<details>
<summary><strong>Phase 5 — Performance</strong></summary>

The platform should feel fast. Optimise:

- Image loading
- Map performance
- Database queries
- Caching (Cloudflare)
- Lazy loading
- Mobile responsiveness

**Target: page loads under 2 seconds on a typical connection.** This matches the existing performance targets already documented (map initial load <2s, API search <300ms p95) — treat this phase as verifying those targets are actually met under real data volume, not just designed for.

Cloudflare caching here means CDN/cache behaviour at the edge — this is unrelated to the DNS-only requirement in the hosting rules (`marketplays_cursor_rules.md` Section 2.4). Caching static assets through Cloudflare is fine; do not re-enable Cloudflare **proxying** of the live app traffic to get it — that's still off-limits per the hosting decision already made.

</details>

---

<details>
<summary><strong>Phase 6 — Security</strong></summary>

Complete:
- Authentication rules (now Clerk-based — see Conflicts section)
- Database permissions (Supabase row-level security)
- Stripe webhook validation
- Input validation
- Rate limiting
- Image validation
- GDPR compliance
- Privacy policy
- Terms of service

Most of the technical rules here (rate limits, file upload validation, parameterised queries, RBAC) are already specified in `marketplays_cursor_rules.md` Section 5.1 — this phase is about confirming they're actually implemented and testing them, not redesigning them. GDPR/privacy policy/ToS are new items not covered elsewhere in the existing docs — these need actual legal-facing content, not just engineering work; flag to the human rather than having an agent draft binding legal text unsupervised.

</details>

---

<details>
<summary><strong>Phase 7 — Analytics</strong></summary>

Install:
- Google Analytics 4
- PostHog (product analytics)
- Error monitoring (e.g. Sentry)

Track:
- Sign-ups
- Listings created
- Bookings
- Payments
- Drop-off points
- Conversion rates

This is product/usage analytics for the business — distinct from the in-app buyer/seller "Analytics" dashboards already specified (buyer campaign spend, seller revenue/CIS trend). Don't conflate the two: GA4/PostHog/Sentry are external tools tracking platform health and funnel conversion; the in-app dashboards are user-facing features already built.

</details>

---

<details>
<summary><strong>Phase 8 — QA Testing</strong></summary>

Test every journey end to end. Fix every issue found before launch — this phase gates launch, it doesn't run in parallel with a "launch anyway" decision.

**Seller journey:**
1. Register
2. Create profile
3. Connect Stripe
4. Publish listing
5. Receive booking
6. Receive payout

**Buyer journey:**
1. Register
2. Browse map
3. Filter listings
4. Book
5. Pay
6. Leave review

These two lists are the literal test script for the "Definition of Launch Ready" acceptance criteria below — run them as actual manual (or automated end-to-end) test passes, not a design review.

</details>

---

<details>
<summary><strong>Nice-to-Have (After Launch)</strong></summary>

**Do not delay launch for any of these.** Plan them, don't build them yet:

- AI pricing suggestions
- AI-generated listing descriptions
- AI campaign recommendations
- Waitlist/referral programme
- Saved searches
- Favourite listings
- Mobile app
- White-label portals
- API for enterprise customers

Note: "AI pricing suggestions" and "AI-generated listing descriptions" map directly onto the Pricing sub-agent and Listing Optimisation sub-agent already designed in `marketplays_ai_agents_architecture.md` Section 4 — when this work does start, that document is the architecture to build against, not a fresh design. Saved searches are also already specified visually in `marketplays_visual_redesign_spec.md` Section 5.2 (the sidebar filter panel) — the UI exists in the design reference even though it's post-launch scope for logic.

</details>

---

<details>
<summary><strong>Definition of "Launch Ready"</strong></summary>

The platform is ready when a seller can:
1. Sign up
2. Create a profile
3. Connect Stripe
4. Publish a listing
5. Receive a booking
6. Get paid

And a buyer can:
1. Sign up
2. Search the map
3. Filter results
4. Book
5. Pay
6. Track the campaign
7. Leave a review

**If those two end-to-end journeys work reliably, launch and begin onboarding sellers.** Everything else — admin polish, notifications, performance headroom beyond the 2-second target, analytics depth — improves based on real user feedback after that point. Do not gold-plate Phases 2–7 in search of perfection before these two journeys are proven; that's the opposite of this roadmap's intent.

</details>

---

<details>
<summary><strong>Conflicts / Notes vs Earlier Docs</strong></summary>

This roadmap surfaces one real conflict with earlier documentation, worth resolving explicitly rather than leaving ambiguous:

| Item | Earlier doc said | This roadmap says | Which wins |
|---|---|---|---|
| Auth provider | Custom JWT (15min access / 7-day refresh) + bcrypt cost factor 12, per `Marketplays_Developer_Specification.docx` and `marketplays_cursor_rules.md` Section 5.1 | **Clerk** authentication | **This roadmap** — Clerk is what's actually implemented; treat the JWT/bcrypt spec as superseded for authentication specifically |

**What does *not* change because of the Clerk switch:** role-based access control still needs to gate buyer/seller/admin endpoints server-side (Clerk's session/role claims replace the JWT role claim, same enforcement principle); the booking state machine, CIS formula, DB schema, and commission logic are all identity-provider-agnostic and unaffected. Update `marketplays_cursor_rules.md` Section 5.1's auth bullet to reference Clerk next time that file is revised, so future agents aren't told to "finish" a JWT system that was replaced.

No other conflicts identified — this roadmap is additive/sequencing guidance on top of the existing rules, not a redesign.

</details>

---

<details>
<summary><strong>Quick Reference</strong></summary>

| Need | Where to look |
|---|---|
| The one rule that matters most | Section 0 |
| What "done" looks like for MVP | Phase 1 + Definition of Launch Ready |
| Admin panel scope | Phase 2 |
| Stripe Connect completion | Phase 3 |
| Notification list (email + in-app) | Phase 4 |
| Performance targets | Phase 5 |
| Security checklist | Phase 6 |
| Analytics tooling (GA4/PostHog/Sentry) | Phase 7 |
| The literal test scripts | Phase 8 |
| What NOT to build yet | Nice-to-Have |
| Clerk vs JWT conflict | Conflicts section |

</details>

---

*Launch-readiness roadmap for Marketplays. Governs sequencing and priority only — pair with `marketplays_cursor_rules.md` for mechanics, `marketplays_visual_redesign_spec.md` for UI, and `marketplays_ai_agents_architecture.md` for the explicitly-deferred agent layer.*
