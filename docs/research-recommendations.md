# Marketplays — Research Recommendations

> Actionable stack guidance for the Marketplays monorepo (`apps/web`, `apps/api`).  
> Sourced against `docs/marketplays_cursor_rules.md` Sections 1, 2, 10 and current vendor docs as of **July 2026**.  
> Hard constraints: backend on **Vercel** (not Railway for the API); Cloudflare **DNS-only** (grey cloud); money as **integer pence**; booking status enum fixed per Section 1.3.

---

## 1. FastAPI on Vercel Python / Fluid Compute

### Entrypoint
- Export a FastAPI instance named **`app`** from a supported file: `app.py`, `index.py`, `server.py`, `main.py`, `wsgi.py`, or `asgi.py` (also under `src/`, `app/`, or `api/`).
- For Marketplays monorepo layout (`apps/api/...`), set explicitly in `apps/api/pyproject.toml`:

```toml
[tool.vercel]
entrypoint = "app.main:app"   # adjust to actual module path
```

- Do **not** rely on Vercel guessing the entrypoint in a nested monorepo package.

### `vercel.json` (API project `marketplays-api`)
- Key `functions` by the **resolved entrypoint file**, not by `/api/*` route patterns:

```json
{
  "$schema": "https://openapi.vercel.sh/vercel.json",
  "fluid": true,
  "functions": {
    "app/main.py": {
      "maxDuration": 60,
      "excludeFiles": "{tests/**,**/__pycache__/**,**/*.pyc}"
    }
  },
  "crons": [
    { "path": "/api/cron/booking-transitions", "schedule": "1 0 * * *" },
    { "path": "/api/cron/extend-availability", "schedule": "0 1 * * *" }
  ]
}
```

- Map the two Section 2 / 5.4 jobs: daily booking state-machine transitions (`00:01` UTC → use `1 0 * * *`) and 90-day availability window extension.
- Cron timezone is **always UTC**. Verify Auth: require `CRON_SECRET` (or check `User-Agent: vercel-cron/1.0`) so paths are not publicly callable.
- Hobby plan: crons max **once/day** and fire within ±59 min of the hour. Marketplays needs reliable daily `00:01` transitions → plan on **Pro** for the API project.
- Crons run on **production** only, not preview.

### Fluid Compute & cold starts
- Fluid is **default** for new projects (since Apr 2025). Keep it on: concurrent requests on one instance cut cold starts and cost for I/O-bound FastAPI + Supabase work.
- Still expect cold starts after idle; mitigate by: lean deps (bundle ≤500MB uncompressed; Large Functions 5GB only if explicitly enabled), connection pooling (Supabase pooler / PgBouncer, not a long-lived process pool assumption), and avoiding heavy imports at module top-level.
- Shutdown cleanup after SIGTERM is capped at **~500ms** — do not depend on long teardown in lifespan handlers.
- Prefer `python3.12`+ for extended `maxDuration` support on Pro.

### What NOT to run in the Vercel Function
Per Section 2.3 — keep these **off** the request path / cron:

| Work | Where instead |
|---|---|
| Proof-video transcoding / malware scan | Dedicated worker (Railway free tier **only for workers**, or Inngest/QStash) |
| Multi-step AI agent chains (V1.1+) that may exceed duration | Queue + worker; API returns job id |
| Long Stripe payout reconciliation loops | Cron chunked jobs or queue |
| Persistent Redis/Celery workers | External worker service |

API stays request/response: webhooks, CRUD, map search, booking create, short cron ticks.

---

## 2. Mapbox GL JS — Marketplace Map UI

Align with Buyer rules (Section 6) and colour tokens (Section 3.1).

### Clustering
- Use a **GeoJSON source with `cluster: true`** (or Supercluster) for listing pins — not DOM `Marker`s once past ~100 points.
- Recommended: `clusterMaxZoom: 14`, `clusterRadius: 50`.
- **Cluster click → zoom in only**; never open `ListingSlideInPanel`. Only an unclustered pin opens the panel (Section 6).
- Cap client payload: API returns **max 20** list rows for cards, but map pins may need a higher pin-only cap (e.g. 500–2000 GeoJSON features per viewport). Document a hard server cap; if UK-wide density exceeds ~10k visible, move to vector tiles later.

### Viewport / bbox queries
- Primary query: `GET /api/ad-spaces?bbox=west,south,east,north&zoom=…` (+ filters AND across types, OR within multi-select — Section 5.4).
- Re-fetch rules (Section 6): pan **>25%** of viewport **or** zoom change **≥2 levels**, debounced **400ms**. Do not query on every `move` pixel.
- On `moveend` / idle: `map.getBounds()` → `[west, south, east, north]` → `source.setData(geojson)`.
- Empty filter set → all published listings in default viewport bbox — never empty result for “no filters”.

### Pin colours (exact tokens)
| State | Token | Hex |
|---|---|---|
| Available | `--pin-available` | `#22C55E` |
| Limited | `--pin-limited` | `#F59E0B` |
| Booked | `--pin-booked` | `#EF4444` |
| New (null CIS) | `--pin-new` | `#7C3AED` |
| Selected | brand blue | `#1A56DB` |

Recalculate colours on every filter apply (no stale colour cache). Prefer **symbol / circle layers** with data-driven `paint` over HTML markers.

### Performance caps
- Dynamic-import Mapbox; load style + first bbox fetch in parallel with map init.
- Always `map.remove()` on route unmount (App Router SPA leaks otherwise).
- Reuse one popup / slide-in instance; use feature-state for hover, not layer thrash.
- Target: map interactive **<2s** (global perf target). Prefer Mapbox GL JS **v3**; drop `@types/mapbox-gl` if using ≥3.5 (first-party types). WebGL2 required.

---

## 3. Stripe Connect — Separate Charges and Transfers

### Hold funds until `Completed`
Marketplays is MoR on the platform; seller payout only after booking reaches **`Completed`** (buyer rating or 72h auto-approve), or admin dispute resolution (`Disputed → Completed`).

1. **Charge** on platform: PaymentIntent / Checkout with `transfer_group = booking_{id}` and amounts in **integer pence** (`currency=gbp`).
2. On `payment_intent.succeeded` → booking `Pending_Payment → Confirmed` (Section 5.2). Funds sit on **platform balance** — do **not** create a Transfer yet.
3. On transition to **`Completed`** (or dispute Approve Seller): create `Transfer` with:
   - `amount` = seller share in pence (gross − platform commission)
   - `destination` = seller Connect account id
   - `transfer_group` = same `booking_{id}`
   - **`source_transaction`** = charge id from the original PaymentIntent — queues transfer until charge funds are available; avoids “insufficient balance” failures
4. Partial dispute payouts: transfer reduced amount; remainder stays as platform fee / refund path per admin resolution.
5. Never invent status strings — only enum values in Section 1.3.

### Webhook signature validation
- Endpoint: FastAPI route reading **`await request.body()`** (raw bytes) — never a Pydantic body model or `request.json()` before verify.
- `stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)` → on failure return **HTTP 400**.
- Idempotency: persist `event.id`; ignore duplicates. Stripe retries for days.
- Wire at minimum: `payment_intent.succeeded`, `payment_intent.payment_failed`, `account.updated` (Connect), plus transfer success/failure if used.
- Production webhook URL only on production Vercel env; preview uses Stripe **test** mode + separate webhook secret (Section 2.5).

### Connect onboarding
- Use **Express** (or Controllers) + **Account Links** (or embedded onboarding) for UK sellers.
- Publish guard (Section 7): block listing publish until `charges_enabled` (and payout readiness as required) on the connected account.
- Store `stripe_account_id` on seller; never put `STRIPE_SECRET_KEY` in the Next.js client bundle.
- Platform in **GB** is supported for SCT; keep connected accounts in supported regions for cross-border rules.

---

## 4. Supabase PostGIS — Radius / Bbox Listing Search

### Schema
- Store listing location as **`geography(Point, 4326)`** (meters semantics) — best fit for UK radius filters.
- Columns: `location geography(Point,4326) NOT NULL`, plus optional denormalised `lat`/`lng` for debug only (do not query those for distance).

### Indexes (required)
```sql
CREATE INDEX listings_location_gix ON listings USING GIST (location);
-- If filtering published map results heavily:
CREATE INDEX listings_published_location_gix
  ON listings USING GIST (location)
  WHERE status = 'published' AND suspended_at IS NULL;  -- match actual columns
```

After bulk load: `ANALYZE listings;`. Confirm with `EXPLAIN ANALYZE` — expect Bitmap/Index scan on GiST, not Seq Scan.

### Query patterns
**Radius (filter sidebar):**
```sql
WHERE ST_DWithin(
  location,
  ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
  :radius_meters
)
ORDER BY location <-> ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography
```
- Use **`ST_DWithin` for filter**, `<->` / `ST_Distance` only for sort/display. Never `ST_Distance(...) < r` in `WHERE` (skips index).

**Viewport bbox (map):**
```sql
WHERE location && ST_MakeEnvelope(:west, :south, :east, :north, 4326)::geography
-- or ST_Intersects(location, envelope::geography)
```
Combine with published/not-draft/not-suspended, category OR, price AND, CIS tiers (null CIS included — Section 5.4), paginate list endpoints ≤20; map pin endpoint may return a separate higher cap.

### ORM note
- Prefer SQLAlchemy + GeoAlchemy2 / bound params — **never** string-interpolate WKT from the client.
- Pass lng/lat as floats; build geography server-side.

---

## 5. Next.js 15 App Router + shadcn — Light Marketing / Dark App

### Forced split (Section 3.1)
- Marketing / landing / public listing SEO pages → **light only**.
- Logged-in buyer / seller / admin dashboards → **dark only**.
- Do **not** ship a user theme toggle that lets dashboards go light or marketing go dark.

### Implementation pattern
1. Root `app/layout.tsx`: `next-themes` `ThemeProvider` with `attribute="class"`, `suppressHydrationWarning` on `<html>`.
2. Marketing route group layout: `forcedTheme="light"` (or set `className` without `dark` and disable system).
3. `(buyer)` / `(seller)` / `(admin)` layouts: `forcedTheme="dark"`.
4. shadcn CSS variables in `globals.css` for both `:root` and `.dark`; brand tokens (`--brand-blue`, pin colours) defined once and reused.
5. No ModeToggle on production chrome for Marketplays — forced themes satisfy the brand rule without a switcher.

### App Router gotchas for this split
- Keep map (`useMap`) and dashboards as Client Components under dark layouts; public `/listings/[id]` SSR stays under light marketing shell if that page is public SEO.
- Shared components (`ListingSlideInPanel`, `CISBadge`) must use semantic tokens (`bg-background`, `text-foreground`) so they render correctly in both forced themes.

---

## 6. July 2026 Stack Gotchas (Section 1 stack)

| Area | Gotcha | Marketplays action |
|---|---|---|
| **Next.js 15** | `params`, `searchParams`, `cookies()`, `headers()` are **async** — must `await` (sync shim removed in Next 16) | Await in all `page.tsx` / layouts (`listings/[id]`, campaign routes) |
| **Next.js 15** | `fetch` / GET Route Handlers **uncached by default** | Explicit `cache: 'force-cache'` or `revalidate` for public listing SSR SEO |
| **Next.js 15** | React 19 + hydration stricter | Use `suppressHydrationWarning` only on `<html>` for themes; fix real mismatches |
| **Vercel FastAPI** | Whole API = **one** Function; `maxDuration` keyed by entrypoint file | Don’t configure per-route Python files like Node `/api` |
| **Vercel Cron** | UTC only; Hobby = 1×/day ±59m; Pro for reliable `00:01` | Put booking cron on Pro API project; auth cron paths |
| **Cloudflare** | Orange cloud breaks Vercel SSL | Keep **DNS-only** grey cloud; SSL/TLS **Full** if redirect loops |
| **Mapbox GL JS v3** | WebGL2 required; map load billed on `Map` construct; TS types built-in ≥3.5 | Drop `@types/mapbox-gl`; test Safari private mode terrain quirks |
| **Stripe SCT** | `transfer_group` alone does not hold/delay funds | Always set `source_transaction` on seller Transfer at `Completed` |
| **Stripe webhooks** | Parsed JSON body breaks signatures | FastAPI: raw `request.body()` only |
| **Supabase PostGIS** | `geometry` vs `geography` mismatch skips GiST | Stick to `geography` + meters for radius; cast consistently |
| **Money** | Float GBP causes rounding bugs | Integer **pence** in DB/API; format £ only in UI |
| **Enums** | Synonyms break state machine / agents | Exact booking + category enums from Section 1.3 everywhere |
| **Hosting** | Legacy docs may say Railway for API | API = **Vercel**; Railway only if used later as **worker** for non-request work |
| **Preview envs** | Shared prod Stripe/Supabase = data corruption | Separate Supabase project/schema + Stripe test keys for preview |

---

## Priority checklist (build order)

1. Scaffold `marketplays-api` with named `app` entrypoint + Fluid + Pro cron for booking transitions.  
2. PostGIS `geography` + GiST + `ST_DWithin` / bbox search before map UI polish.  
3. Stripe: charge on book → Transfer + `source_transaction` only on `Completed`; raw-body webhooks.  
4. Map: clustered symbol layer, Section 6 requery rules, Section 3.1 pin colours.  
5. Theme: forced light marketing / forced dark app layouts — no mixed screens.

---

*Reference: [Vercel FastAPI](https://vercel.com/docs/frameworks/backend/fastapi), [Fluid Compute](https://vercel.com/docs/fluid-compute), [Vercel Cron](https://vercel.com/docs/cron-jobs), [Stripe SCT](https://docs.stripe.com/connect/marketplace/tasks/accept-payment/separate-charges-and-transfers), [Mapbox GL JS v3 migrate](https://docs.mapbox.com/mapbox-gl-js/guides/migrate-to-v3/), [shadcn dark mode](https://ui.shadcn.com/docs/dark-mode/next), [Next.js 15](https://nextjs.org/blog/next-15).*
