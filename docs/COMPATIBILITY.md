# Marketplays — Doc compatibility index

Short map of which reference governs what. Do not treat this file as a product spec.

| Document | Governs | Does not govern |
|----------|---------|-----------------|
| `docs/marketplays_cursor_rules.md` | **Mechanics** — stack, enums, booking state machine, CIS, schema, security baseline, portal rules | Launch priority order; UI visual system |
| `docs/marketplays_launch_roadmap.md` | **Sequencing & priority** — stabilise-and-ship phases; Phase 1 MVP journeys first; Conflicts (Clerk vs JWT) | New features; underlying booking/CIS/schema mechanics |
| `docs/marketplays_visual_redesign_spec.md` | **Visual / UX** — style, layout, colour tokens for UI | API, schema, booking state machine |
| `docs/research-recommendations.md` | **Stack research** — why Vercel FastAPI, Mapbox, Stripe SCT, PostGIS | Day-to-day implementation order or UI look |

## How to use together

1. **What to do next / in what order** → launch roadmap (Phase 1 before Nice-to-Have / AI agents).
2. **How it must work** → cursor rules (and topic docs under `docs/` such as `booking-state-machine.md`, `cis-formula.md`).
3. **How it should look** → visual redesign spec (style only).
4. **Why this stack** → research recommendations.

## Auth conflict (pointer only)

Per launch roadmap **Conflicts**: **Clerk** supersedes custom JWT/bcrypt for the authentication provider. Server-side RBAC (buyer/seller/admin) remains required. Migration plan: `docs/clerk-migration-plan.md` (JWT still live until cutover).

## Gap checklists (roadmap compatibility)

| Document | Covers |
|----------|--------|
| `docs/phase-1-mvp-gap-checklist.md` | Phase 1 auth / seller / buyer / listings vs Launch Ready |
| `docs/phase-2-4-gap-checklist.md` | Admin, payments, notifications |
| `docs/phase-5-8-hardening-checklist.md` | Performance, security, analytics, QA scripts |
| `docs/launch-ready-definition.md` | Definition of Launch Ready + Nice-to-Have freeze |

## Agent entrypoints

- `AGENTS.md` — path ownership + sequencing/auth pointers
- `.cursor/rules/global.mdc` — always-on stack + sequencing/auth pointers
- `.cursor/rules/backend.mdc` — API mechanics + Clerk auth pointer
