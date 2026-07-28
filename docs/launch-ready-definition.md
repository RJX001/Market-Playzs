# Definition of Launch Ready

> Source: `docs/marketplays_launch_roadmap.md` — **Definition of "Launch Ready"** + **Nice-to-Have**.  
> Companion hardening checklist: [`docs/phase-5-8-hardening-checklist.md`](./phase-5-8-hardening-checklist.md).  
> Phase 1 MVP gaps: [`docs/phase-1-mvp-gap-checklist.md`](./phase-1-mvp-gap-checklist.md) (when present).

This file restates what "launch ready" means for Marketplays and what must **not** be built yet. It does not expand product scope.

---

## The bar

The platform is ready when the two end-to-end journeys below work **reliably**. Then launch and begin onboarding sellers.

Everything else — admin polish, notifications, performance headroom beyond the 2-second target, analytics depth — improves from real user feedback after that point.

---

## Seller journey (must work)

A seller can:

1. Sign up
2. Create a profile
3. Connect Stripe
4. Publish a listing
5. Receive a booking
6. Get paid

Phase 1 acceptance also times first publish: a new seller creates a **live listing in under 10 minutes** (testable in Phase 8 QA).

Executable Pass/Fail script: [`docs/phase-5-8-hardening-checklist.md`](./phase-5-8-hardening-checklist.md) — Phase 8 Seller journey.

---

## Buyer journey (must work)

A buyer can:

1. Sign up
2. Search the map
3. Filter results
4. Book
5. Pay
6. Track the campaign
7. Leave a review

Executable Pass/Fail script: [`docs/phase-5-8-hardening-checklist.md`](./phase-5-8-hardening-checklist.md) — Phase 8 Buyer journey (+ extended tracking rows).

---

## Cross-link — Phase 1 gap checklist

Before treating Phases 2–8 as launch blockers, close Phase 1 gaps:

- **Primary:** [`docs/phase-1-mvp-gap-checklist.md`](./phase-1-mvp-gap-checklist.md) — auth, seller onboarding, buyer journey, listing pages (Done / Partial / Missing + evidence).
- **Roadmap detail:** `docs/marketplays_launch_roadmap.md` Phase 1 (sections 1.1–1.4).
- **Mechanics (unchanged by this definition):** booking state machine, CIS, publish guard — `docs/marketplays_cursor_rules.md`.

If the Phase 1 gap checklist is not in the repo yet, create/complete it before gold-plating later phases.

---

## Do not gold-plate Phases 2–7 first

**Phases 2–7 must not be gold-plated before the two journeys above work.**

| Phase | Role relative to launch |
|-------|-------------------------|
| **1** | Blocks meaningful progress — finish journeys |
| **2–4** | Can parallelise once journeys work; polish is not a pre-journey gate |
| **5–8** | Cross-cutting hardening — continuous, not a reason to delay proving journeys |
| **Nice-to-Have / AI agents** | Explicitly after launch-ready |

Opposite of intent: polishing admin analytics, GA4 funnels, or edge-case performance before a seller can publish and get paid.

---

## Do not build yet — Nice-to-Have (OUT OF SCOPE)

**Do not delay launch for any of these. Plan them; do not build them yet.**

| Item | Notes |
|------|--------|
| AI pricing suggestions | Maps to Pricing sub-agent in `marketplays_ai_agents_architecture.md` — build against that doc later |
| AI-generated listing descriptions | Maps to Listing Optimisation sub-agent — same |
| AI campaign recommendations | Post-launch |
| Waitlist / referral programme | Post-launch |
| Saved searches | Visual reference may exist in redesign spec; logic is post-launch |
| Favourite listings | Post-launch |
| Mobile app | Post-launch |
| White-label portals | Post-launch |
| API for enterprise customers | Post-launch |

Also out of scope until journeys are launch-ready: the in-product **Buyer/Seller Agent** layer (`docs/marketplays_ai_agents_architecture.md`).

---

## Related docs

| Need | Doc |
|------|-----|
| Sequencing / mandate | `docs/marketplays_launch_roadmap.md` section 0 |
| Phase 1 gaps | `docs/phase-1-mvp-gap-checklist.md` |
| Phases 5–8 hardening + QA scripts | `docs/phase-5-8-hardening-checklist.md` |
| Hosting (unchanged: Vercel + Cloudflare DNS-only) | `docs/deployment.md` |
| Auth IdP = Clerk (roadmap wins over JWT spec) | Roadmap Conflicts section |
