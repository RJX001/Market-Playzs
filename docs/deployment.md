# Marketplays — Deployment Guide

Authoritative rules: `docs/marketplays_cursor_rules.md` **Section 2** (Deployment) and **Section 10** (Quick Reference).

**Launch sequencing:** Work order and “what to ship before polish” live in `docs/marketplays_launch_roadmap.md` (Phase 1 journeys first; Phases 5–8 are hardening, not a reason to change hosting). Definition of done: `docs/launch-ready-definition.md`. This guide’s hosting decisions stay **Vercel** (`marketplays-web` + `marketplays-api`) with Cloudflare **DNS-only** (grey cloud) — do not enable proxy/CDN mode for app traffic.

---

## Architecture

| Vercel project | Root directory | Domain | Runtime |
|----------------|----------------|--------|---------|
| `marketplays-web` | `apps/web` | `marketplays.com`, `www.marketplays.com` | Next.js 15 |
| `marketplays-api` | `apps/api` | `api.marketplays.com` | FastAPI (Vercel Python / Functions) |

Do **not** merge web and API into one Vercel project. Separate projects keep logs, scaling, and Fluid Compute settings independent.

---

## FastAPI entrypoint (Vercel)

- Primary app: `apps/api/app/main.py` — FastAPI instance **must** be named `app`.
- Local / uvicorn: `uvicorn app.main:app --reload --port 8000` (from `apps/api`).
- Vercel discovery fallback: `apps/api/api/index.py` re-exports `app`.
- Explicit path in `apps/api/pyproject.toml`: `[tool.vercel] entrypoint = "app/main.py"`.

---

## Cloudflare DNS (DNS-only / grey cloud)

Cloudflare is registrar **and** DNS manager. Do **not** move nameservers to Vercel.

1. In each Vercel project → Settings → Domains, add the domains above.
2. In Cloudflare DNS, create **exactly** the records Vercel shows (typically):
   - Apex `marketplays.com` → A record (Vercel IP)
   - `www` → CNAME → Vercel
   - `api` → CNAME → `marketplays-api` Vercel target
3. Set **every** Marketplays record to **DNS only (grey cloud)** — never Proxied (orange cloud). Proxying breaks Vercel SSL issuance/renewal.
4. Cloudflare SSL/TLS mode: **Full** (not Flexible). “Too many redirects” almost always means Flexible was left on.
5. Do not enable Cloudflare proxy caching / WAF / Bot Fight Mode against this traffic while DNS-only.

---

## Environment separation

| Vercel environment | Stripe | Supabase | Notes |
|--------------------|--------|----------|-------|
| **Production** | Live keys | Production project | Webhooks → `https://api.marketplays.com/...` only |
| **Preview** | **Test** keys | Separate project **or** isolated schema | Never point preview at prod Stripe/Supabase |
| **Development** | Test keys | Local / preview Supabase | Local `.env` files only |

Configure production Stripe webhook secret and production `DATABASE_URL` / `SUPABASE_*` **only** on the Production environment in Vercel — not Preview/Development.

### Frontend (`apps/web`) — copy to `.env.local`

Template: `apps/web/.env.local.example`

```
NEXT_PUBLIC_MAPBOX_TOKEN=
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
```

On Vercel Preview, set `NEXT_PUBLIC_API_URL` to the preview API URL (or a stable preview API), not production.

### Backend (`apps/api`) — copy to `.env`

Template: `apps/api/.env.example`

```
DATABASE_URL=
SUPABASE_URL=
SUPABASE_SERVICE_KEY=
JWT_SECRET=
JWT_REFRESH_SECRET=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_CONNECT_CLIENT_ID=
SENDGRID_API_KEY=
MAPBOX_SECRET_TOKEN=
CRON_SECRET=
ENVIRONMENT=development
CORS_ORIGINS=
```

`CRON_SECRET` (optional until handlers ship): Vercel Cron should send `Authorization: Bearer <CRON_SECRET>`; handlers must reject unauthenticated calls.  
`ENVIRONMENT`: `development` | `preview` | `production` — drives Secure refresh-cookie flag.  
`CORS_ORIGINS`: comma-separated extra origins (Vercel preview URLs).

Never commit real `.env` / `.env.local`. Never expose Stripe secret keys, Supabase service role, or Mapbox secret token to the Next.js client bundle.

## Backups and restore

Confirm **daily backups** are enabled on the production Supabase project (Dashboard → Database → Backups; PITR on paid plans). Snapshots are the source of truth for Postgres data — Vercel deploys are not a data backup. To restore: choose a snapshot in the Supabase dashboard, restore to a new project (preferred) or overwrite after a written freeze, then point production `DATABASE_URL` / `SUPABASE_*` at the restored instance and reconcile Stripe/webhook events that landed after the snapshot timestamp before reopening traffic.

---

## Vercel Cron stubs

Defined in `apps/api/vercel.json` (API project only):

| Schedule (UTC) | Path | Purpose |
|----------------|------|---------|
| `1 0 * * *` (00:01 daily) | `/api/cron/booking-transitions` | Booking state machine daily transitions (Confirmed→Live, Live→Awaiting_Proof, timeouts) — **TODO handler** |
| `0 0 * * *` (00:00 daily) | `/api/cron/extend-availability` | Extend each listing’s availability window to 90 days ahead — **TODO handler** |

Stub routes live on the FastAPI `app` in `apps/api/app/main.py`. Backend agent implements real logic per Section 5.2.

---

## Root routing (`apps/web`)

| Path | Intent |
|------|--------|
| `/` | Marketing home (current `src/app/page.tsx` is a placeholder until marketing lands) |
| `/map` | Buyer live-map entry (Section 6) — create with Buyer portal |
| `/dashboard/seller` | Seller revenue dashboard entry (Section 7) |

If marketing is not ready and `/` must not show the Next.js starter forever, either replace the marketing page or redirect `/` → `/map` and document the change here. Do **not** collapse marketing and app chrome into one light/dark mix (Section 3.1).

---

## Deploy checklist

### One-time setup

- [ ] Create Vercel project `marketplays-web` — Root Directory `apps/web`, Framework Next.js
- [ ] Create Vercel project `marketplays-api` — Root Directory `apps/api`, Python / FastAPI
- [ ] Connect both to the same GitHub repo; Production branch = `main`
- [ ] Add domains in Vercel; mirror DNS in Cloudflare as **DNS only**
- [ ] Cloudflare SSL/TLS = **Full**
- [ ] Create separate Supabase project (or schema) for Preview
- [ ] Create Stripe test + live Connect apps; webhooks per environment
- [ ] Set Production vs Preview env vars independently (tables above)
- [ ] Confirm FastAPI health: `GET https://api.marketplays.com/health` → `{"status":"ok"}`
- [ ] Confirm web: `https://marketplays.com` loads marketing `/`

### Every release

- [ ] Preview deploy uses Stripe **test** + non-prod Supabase
- [ ] Production Stripe webhook endpoint points only at production API
- [ ] Cron paths still match `apps/api/vercel.json` after route refactors
- [ ] No secrets in client bundle (`NEXT_PUBLIC_*` only for publishable values)
- [ ] `apps/web`: `npm run typecheck` and `npm run lint` pass
- [ ] Long-running work (malware scan, heavy video, long agent chains) **not** in Vercel Functions — use a worker/queue (Section 2.3)

### Local

```bash
# Web
cd apps/web && cp .env.local.example .env.local && npm install && npm run dev

# API
cd apps/api && cp .env.example .env
python -m venv .venv && .\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
