# Clerk Migration Plan — Marketplays Auth Compatibility

> **Status:** Compatibility / planning only. Custom JWT + bcrypt remains the live provider until cutover.  
> **Roadmap authority:** `docs/marketplays_launch_roadmap.md` Phase 1.1 + Conflicts — **Clerk wins** as the target auth *provider*.  
> **Rules authority:** `docs/marketplays_cursor_rules.md` Section 5.1 still owns **RBAC and rate-limit principles**; only the identity provider changes.  
> **Out of scope here:** AI agents, booking state machine changes, CIS formula, schema redesign, production Google OAuth wiring without env keys.

---

## 1. Audit — What Exists Today

### 1.1 Backend (working JWT / bcrypt)

| Piece | Path | Behaviour |
|-------|------|-----------|
| Routes | `apps/api/app/api/auth.py` | `POST /api/auth/register`, `/login`, `/refresh`, `/logout` |
| Service | `apps/api/app/services/auth_service.py` | bcrypt cost **12**; HS256 access JWT (**15 min**); refresh JWT (**7 days**) in HttpOnly cookie `refresh_token` (path `/api/auth`); never returns refresh in JSON |
| Middleware deps | `apps/api/app/middleware/auth.py` | `get_current_user`, `require_roles`, aliases `RequireBuyer` / `RequireSeller` / `RequireAdmin` |
| Route deps (in use) | `apps/api/app/api/deps.py` | `get_current_user` + `require_role(...)` — **this** is what listings/bookings/admin/payments import |
| Schemas | `apps/api/app/schemas/auth.py` | Register with `role: buyer \| seller` (blocks admin self-register); login; `AccessTokenResponse` |
| User row | `apps/api/app/models/user.py` | `email`, **required** `password_hash`, single `role` enum, `is_suspended`, Stripe Connect fields |
| Rate limits | `apps/api/app/middleware/rate_limit.py` | Login 5/IP/15min; authenticated 100/min per user id (Section 5.1) |
| Tests | `apps/api/tests/test_auth.py` | Token create/decode + login rate-limit smoke |

**Access token claims today:** `sub` (user UUID), `role`, `email`, `type: access`, `iat`, `exp`.

**Protected API surface:** Bearer access token → decode HS256 → load `users` row → reject if missing/suspended → `require_role` gate. Routers using `deps.require_role`: `listings`, `bookings`, `availability`, `payments`, `admin`, `cis`.

**Note:** `middleware/__init__.py` comments are stale (still mention X-User-Id header stubs). Live enforcement is JWT via `deps.py` / `middleware/auth.py`.

### 1.2 Frontend (UI shells, not wired to API)

| Page | Path | Notes |
|------|------|-------|
| Login | `apps/web/src/app/auth/login/page.tsx` | Email/password form — **no** `fetch` / Clerk / token storage |
| Buyer register | `apps/web/src/app/auth/register/page.tsx` | Hidden `role=buyer` — UI only |
| Seller register | `apps/web/src/app/auth/register/seller/page.tsx` | Hidden `role=seller` + business name — UI only |

- No `@clerk/*` packages in `apps/web/package.json`.
- Role switcher UI exists: `RoleToggle` / `PortalHeader` — **navigation only** (links to buyer/seller/admin homes). No session `active_role` update.
- Admin client has a commented Bearer header placeholder (`admin-api.ts`).

### 1.3 Doc conflict (resolved by roadmap)

| Earlier (Section 5.1) | Roadmap Conflicts | This plan |
|-----------------------|-------------------|-----------|
| Custom JWT + bcrypt | **Clerk** is the target provider | Keep JWT live until cutover; migrate verification into existing `require_role` path |

**Unchanged by Clerk:** booking state machine (5.2), CIS (5.3), DB schema / commission logic, server-side RBAC principle, rate-limit *targets* (re-map login limit to Clerk-facing surfaces).

---

## 2. Target Architecture

### 2.1 Product requirements (Phase 1.1)

1. **Clerk** as IdP — Google sign-in primary; email/password optional (do not block launch if Google is solid).
2. **User profiles** — continue to own Marketplays profile data in Postgres (`users`), linked to Clerk identity.
3. **Buyer / seller role at signup** — capture intended role during / immediately after Clerk sign-up (mirror today’s `/auth/register` vs `/auth/register/seller`).
4. **Role switching** — header pill (`RoleToggle`) becomes session-aware: switching updates **active portal context** and only allows destinations the user is entitled to (admin remains server-gated).

### 2.2 Identity vs authorization split

```
Clerk (identity + session)          Marketplays API (authorization)
─────────────────────────           ────────────────────────────────
Google / optional email             Verify Clerk JWT / session
Clerk user id (sub)                 Map → users.id (+ clerk_user_id)
Optional publicMetadata.role        Source of truth for RBAC: users.role
                                    + optional session active_role
                                    require_role / RequireBuyer|Seller|Admin
                                    is_suspended checks
                                    rate limit 100/min
```

**Principle:** UI never authorises. Clerk proves *who*; FastAPI `require_role` still proves *may call this route*.

### 2.3 Role model (recommended for dual-portal UX)

Today: one `users.role` per account.

For role switching without breaking existing `require_role`:

| Concept | Storage | Used by |
|---------|---------|---------|
| **Canonical role** | `users.role` (`buyer` \| `seller` \| `admin`) | Signup default; admin assignment; Stripe Connect eligibility |
| **Active portal** | Session / cookie / Clerk `publicMetadata.active_role` or short-lived client preference | `RoleToggle` UI + optional claim checked only when both buyer+seller capabilities exist |
| **Capabilities** | Prefer start: single role as today; later optional `roles[]` or `can_sell` / `can_buy` flags if dual-role accounts are required | Gate which RoleToggle targets are valid |

**MVP-compatible approach (no schema change required for cutover):**

1. Signup sets `users.role` to `buyer` or `seller` (same as `RegisterRequest.role`).
2. `RoleToggle` for a pure buyer hides or no-ops Seller until they complete a “become seller” flow that **updates** `users.role` (or a future dual-role column) via a dedicated API — not via client-only navigation.
3. Admin role is never self-assigned (same as today).
4. When calling `/api/*`, Bearer token maps to DB user; `require_role` uses **DB role** (or explicit active_role only if DB says user may use that portal).

Do **not** invent new booking statuses or alter CIS while adding Clerk.

---

## 3. FastAPI: Verify Clerk and Keep `require_role`

### 3.1 Compatibility layer

Stub module: `apps/api/app/services/clerk_compat.py` (TODOs only until keys exist).

Intended surface:

```text
verify_clerk_bearer(token) -> ClerkIdentity   # sub, email, … via JWKS / clerk backend API
ensure_local_user(db, identity, signup_role?) -> User
resolve_authenticated_user(credentials, db) -> CurrentUser / AuthenticatedUser
```

### 3.2 Dual-mode `get_current_user` (during migration)

Keep JWT routes and HS256 verification until cutover:

1. If `Authorization: Bearer <token>` present:
   - Try **Clerk** verification when `CLERK_SECRET_KEY` (and JWKS issuer) configured.
   - Else / fallback: existing `auth_service.decode_access_token` (HS256).
2. Resolve local `users` row:
   - Clerk path: lookup by future `clerk_user_id` (or email bridge during migration); create on first authenticated hit only via controlled signup webhook/endpoint.
   - JWT path: lookup by `sub` UUID (current behaviour).
3. Apply `is_suspended` + `check_user_rate_limit(str(user.id))`.
4. Return same `CurrentUser` / `AuthenticatedUser` shape so **all** `require_role(...)` call sites stay unchanged.

Prefer a single implementation path: have `deps.get_current_user` and `middleware.auth.get_current_user` call the same resolver to avoid drift.

### 3.3 Clerk token verification (implementation notes — not done yet)

- Prefer **Clerk JWT** (session token or backend API JWT) with JWKS from Clerk Frontend API issuer.
- Validate `azp` / authorized parties against Next.js origin(s).
- Never trust client-supplied `role` headers; map role from DB after identity is proven.
- Optional: Clerk webhook `user.created` / `user.updated` to sync email / soft-delete — still write through service layer, not raw SQL strings.

### 3.4 What stays on Section 5.1 principles

| Principle | After Clerk |
|-----------|-------------|
| RBAC on every protected route | Unchanged — `require_role` |
| Login abuse limit | Apply to any remaining password endpoints **and** consider Clerk Dashboard / bot protection for hosted UI; keep IP throttle on any custom bridge endpoints |
| 100 req/min authenticated | Keep, keyed by local `users.id` |
| No password hints in logs | N/A for Google; still apply if email/password via Clerk |
| Stripe webhook signature rules | Unrelated — unchanged |

---

## 4. Environment Variables (templates only)

### 4.1 Web (`apps/web/.env.local.example`)

```bash
NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=
CLERK_SECRET_KEY=
# Optional when using Clerk’s Next.js helpers:
# NEXT_PUBLIC_CLERK_SIGN_IN_URL=/auth/login
# NEXT_PUBLIC_CLERK_SIGN_UP_URL=/auth/register
# NEXT_PUBLIC_CLERK_AFTER_SIGN_IN_URL=/buyer/map
# NEXT_PUBLIC_CLERK_AFTER_SIGN_UP_URL=/buyer/map
```

### 4.2 API (`apps/api/.env.example`)

```bash
CLERK_SECRET_KEY=
# Optional: Clerk Frontend API / JWT issuer for JWKS (e.g. https://xxx.clerk.accounts.dev)
CLERK_JWT_ISSUER=
# Optional authorized party (Next.js origin)
CLERK_AUTHORIZED_PARTY=
```

Until these are set, **do not** enable Google OAuth production wiring or disable JWT.

Existing JWT vars remain required for current auth: `JWT_SECRET`, `JWT_REFRESH_SECRET`.

---

## 5. Migration Steps (keep `/api/*` RBAC working)

Ordered so the app never loses working auth mid-flight.

### Phase A — Compatibility (this agent / current work)

1. Document plan (this file).
2. Add empty Clerk keys to `.env.example` templates.
3. Add `clerk_compat.py` stub (TODOs).
4. **Do not** delete `/api/auth/*` JWT routes.
5. **Do not** remove bcrypt / HS256 code paths.

### Phase B — Frontend Clerk shell (needs real keys in local/Vercel)

1. Install `@clerk/nextjs` when keys are available.
2. Wrap app with `ClerkProvider`; protect dashboard route groups.
3. Replace static auth page forms with Clerk `<SignIn>` / `<SignUp>` (or hosted) — pass `role` via unsafe metadata / query for post-signup provisioning.
4. API client: send Clerk session JWT as `Authorization: Bearer`.
5. Wire `RoleToggle` to portal entitlement checks (still server-enforced).

### Phase C — API dual verification

1. Implement `clerk_compat.verify_*` with JWKS when `CLERK_SECRET_KEY` set.
2. Point `deps.get_current_user` at dual-mode resolver.
3. Add provisioning endpoint or webhook: create `users` row with signup role; keep `password_hash` nullable **only after** an explicit migration (schema change is a dedicated DB PR — not implied by this plan’s “schema unchanged for booking/CIS”; linking column `clerk_user_id` is the one expected auth-adjacent additive change).
4. Keep JWT login for existing test users until cutover flag.

### Phase D — Cutover

1. Feature flag e.g. `AUTH_PROVIDER=clerk|jwt|dual` (default `jwt` or `dual` until green).
2. Migrate known users: email match → set `clerk_user_id`; force password reset via Clerk if email mode enabled.
3. Frontend stops calling `/api/auth/login|register|refresh`.
4. Deprecate then remove JWT routes, refresh cookies, bcrypt hashing — **only after** dual mode is proven in preview.
5. Update `marketplays_cursor_rules.md` Section 5.1 auth bullets to reference Clerk (roadmap already asked for this on next rules revision).

### Explicit non-goals during migration

- No changes to booking status enum or transitions.
- No CIS formula changes.
- No commission / Stripe Connect contract changes (only identity of the seller user).
- No AI Buyer/Seller agents.

---

## 6. Signup + Role Switching — Session Logic Sketch

```text
Sign-up (buyer path)     → Clerk user + users.role = buyer
Sign-up (seller path)    → Clerk user + users.role = seller (+ company_name)
Google first-time        → same provisioning; role from signup URL / metadata

RoleToggle click Seller  → if users.role allows seller (or dual capability):
                              navigate to seller home; set active_portal=seller
                           else:
                              send to “become a seller” onboarding (Stripe later)
API call                 → Bearer Clerk JWT → local user → require_role(seller)
                           fails 403 if DB role insufficient regardless of UI pill
```

Admin pill: only meaningful if `users.role == admin`; otherwise hide or 403 on `/api/admin/*`.

---

## 7. Cutover Checklist

- [ ] Clerk keys in Vercel Production + Preview (secret server-only; publishable on web).
- [ ] Google OAuth enabled in Clerk Dashboard (production domains).
- [ ] Dual-mode API verification green in preview.
- [ ] All `require_role` routers still pass with Clerk Bearer.
- [ ] Suspended users still 403.
- [ ] Rate limit 100/min still applied.
- [ ] JWT routes removed only after no clients depend on them.
- [ ] Section 5.1 docs updated to Clerk provider language.
- [ ] Booking/CIS/schema regression smoke from Phase 8 scripts still pass.

---

## 8. Files Touched by Compatibility Pass

| File | Action |
|------|--------|
| `docs/clerk-migration-plan.md` | Created (this document) |
| `apps/api/app/services/clerk_compat.py` | Stub interface + TODOs |
| `apps/api/.env.example` | Empty Clerk template vars |
| `apps/web/.env.local.example` | Created with empty Clerk + existing public templates |
| `.env.example` | Point at Clerk template keys |
| JWT routes / bcrypt | **Unchanged** |

---

*Compatibility Agent 2 — Auth / Clerk. Provider target = Clerk; RBAC principles = Section 5.1; booking/CIS/schema = unchanged.*
