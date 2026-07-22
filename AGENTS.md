# Marketplays — AGENTS.md

Read `docs/marketplays_cursor_rules.md` (or Desktop master rules) before any task.
Always load Section 1 (Global) + Section 2 (Deployment). Load portal/domain sections only for the matching task.

## Stack (authoritative)
- Frontend: Next.js 15 App Router, shadcn/ui, Tailwind — `apps/web`
- Backend: FastAPI on Vercel Python runtime — `apps/api`
- DB: Supabase (PostgreSQL + PostGIS)
- Payments: Stripe Connect (Separate Charges and Transfers)
- Mapping: Mapbox GL JS
- Hosting: Vercel (web + api); DNS: Cloudflare DNS-only (grey cloud)

## Agent path ownership
| Agent | Owns |
|-------|------|
| Buyer | `apps/web/src/app/(buyer)/**`, `apps/web/src/components/buyer/**` |
| Seller | `apps/web/src/app/(seller)/**`, `apps/web/src/components/seller/**` |
| Admin | `apps/web/src/app/(admin)/**`, `apps/web/src/components/admin/**` |
| Backend | `apps/api/**` |
| Shared | `packages/shared/**`, `apps/web/src/components/shared/**` |

## Non-negotiables
- Money in DB = integer pence; format £ only in UI
- Booking status enum exactly as Section 1.3
- Category enum exactly as Section 1.3
- Agents never bypass the API (Section 9) — MVP has no in-product agents
- Marketing pages = light mode; logged-in dashboards = dark mode

## Research
Stack recommendations (Vercel FastAPI, Mapbox, Stripe SCT, PostGIS): `docs/research-recommendations.md`

## Visual redesign
Authoritative visual/UX spec: `docs/marketplays_visual_redesign_spec.md` (supersedes older colour tokens for UI). Style only — do not change API/schema/state machine.
