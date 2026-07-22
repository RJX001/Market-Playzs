# Marketplays — Database Schema

Authoritative constraints: `docs/marketplays_cursor_rules.md` Sections 1.3 and 4.  
ORM models: `apps/api/app/models/`.  
Money: **integer pence only** in the DB; format to £ only in the UI.  
Timestamps: **every table** has `created_at` and `updated_at` (timestamptz, timezone-aware).

Engine: PostgreSQL + PostGIS (Supabase). SQLAlchemy 2.x **sync** (`psycopg2`) — see `apps/api/app/db/session.py`.

---

## Enums

### `user_role`
| Value | Meaning |
|-------|---------|
| `buyer` | Books ad spaces |
| `seller` | Lists ad spaces |
| `admin` | Platform operator |

### `listing_category` (Section 1.3 — exact)
`sports_club` · `gym` · `school` · `shop` · `cafe` · `festival` · `community_event` · `billboard` · `event_venue`

### `listing_status`
`draft` · `published` · `suspended`

### `booking_status` (Section 1.3 — exact; do not invent synonyms)
`Pending_Payment` · `Confirmed` · `Live` · `Awaiting_Proof` · `Awaiting_Buyer_Review` · `Completed` · `Cancelled` · `Refunded` · `Disputed` · `Admin_Flagged`

### `deliverable_status`
`pending` · `uploaded` · `verified`

### `booking_type`
`instant` · `request`

---

## Tables

### `users`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | `gen_random_uuid()` |
| `email` | TEXT NOT NULL UNIQUE | |
| `password_hash` | TEXT NOT NULL | bcrypt cost ≥ 12 |
| `role` | `user_role` NOT NULL | |
| `full_name` | TEXT NOT NULL | |
| `company_name` | TEXT NULL | |
| `phone` | TEXT NULL | |
| `is_suspended` | BOOLEAN NOT NULL DEFAULT false | Admin suspend |
| `stripe_account_id` | TEXT NULL | Stripe Connect Express/Custom account id (sellers) |
| `stripe_onboarding_complete` | BOOLEAN NOT NULL DEFAULT false | Sellers only |
| `stripe_charges_enabled` | BOOLEAN NOT NULL DEFAULT false | Sellers only |
| `stripe_payouts_enabled` | BOOLEAN NOT NULL DEFAULT false | Sellers only |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

Stripe Connect fields live on `users` for sellers (nullable / false for buyers and admins). Publish guard requires a connected Stripe account before a listing can go `published`.

---

### `listings`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `seller_id` | UUID NOT NULL FK → `users.id` | Role must be seller |
| `title` | TEXT NOT NULL | |
| `description` | TEXT NOT NULL | |
| `category` | `listing_category` NOT NULL | Section 1.3 |
| `status` | `listing_status` NOT NULL DEFAULT `draft` | Draft/suspended never returned in buyer queries |
| `booking_type` | `booking_type` NOT NULL DEFAULT `instant` | |
| `price_per_day_pence` | INTEGER NOT NULL | ≥ 0; money in pence |
| `currency` | CHAR(3) NOT NULL DEFAULT `GBP` | |
| `location` | GEOGRAPHY(POINT, 4326) NOT NULL | PostGIS; Mapbox lat/lng |
| `address_line1` | TEXT NULL | |
| `city` | TEXT NULL | |
| `postcode` | TEXT NULL | |
| `audience_size` | INTEGER NULL | |
| `image_urls` | JSONB NOT NULL DEFAULT `[]` | Array of Storage URLs; ≥1 required to publish |
| `cis_score` | INTEGER NULL | **Nullable — never default 0.** Null = "New" |
| `is_cis_overridden` | BOOLEAN NOT NULL DEFAULT false | Must be set with any admin CIS edit + `audit_logs` row |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

Indexes: GIST on `location`; btree on `seller_id`, `status`, `category`, `cis_score`.

---

### `availability`

One row **per date per listing** — never date-range rows. Powers the 90-day rolling window and per-date lock/unlock.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `listing_id` | UUID NOT NULL FK → `listings.id` ON DELETE CASCADE | |
| `date` | DATE NOT NULL | Calendar day (UTC date boundary for storage) |
| `is_available` | BOOLEAN NOT NULL DEFAULT true | Seller unlock / lock inventory |
| `is_locked` | BOOLEAN NOT NULL DEFAULT false | True while held by an active booking |
| `booking_id` | UUID NULL FK → `bookings.id` ON DELETE SET NULL | Set when locked |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

**Unique constraint:** `(listing_id, date)`.

---

### `bookings`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `listing_id` | UUID NOT NULL FK → `listings.id` | |
| `buyer_id` | UUID NOT NULL FK → `users.id` | |
| `seller_id` | UUID NOT NULL FK → `users.id` | Denormalised for payout / queries |
| `status` | `booking_status` NOT NULL DEFAULT `Pending_Payment` | Exact Section 1.3 values |
| `start_date` | DATE NOT NULL | |
| `end_date` | DATE NOT NULL | Inclusive campaign end |
| `total_amount_pence` | INTEGER NOT NULL | Gross charged to buyer |
| `platform_fee_pence` | INTEGER NOT NULL | Platform commission |
| `seller_payout_pence` | INTEGER NOT NULL | Net to seller (transfer amount) |
| `stripe_payment_intent_id` | TEXT NULL | Separate Charges and Transfers |
| `stripe_charge_id` | TEXT NULL | |
| `stripe_transfer_id` | TEXT NULL | Transfer to connected account |
| `stripe_refund_id` | TEXT NULL | |
| `cis_score` | INTEGER NULL | Per-booking CIS contribution (Section 5.3); set on Completed |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

Status transitions: see `docs/booking-state-machine.md` (Section 5.2 only). Clients never PATCH `status` directly.

---

### `reviews`

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `booking_id` | UUID NOT NULL UNIQUE FK → `bookings.id` | One review per booking |
| `listing_id` | UUID NOT NULL FK → `listings.id` | |
| `buyer_id` | UUID NOT NULL FK → `users.id` | |
| `rating` | SMALLINT NOT NULL | 1–5 stars |
| `delivery_score` | NUMERIC(2,1) NOT NULL | **Exactly** `0`, `0.5`, or `1` |
| `comment` | TEXT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

`delivery_score`: `1` = on-time proof, `0.5` = late, `0` = not uploaded. Feeds CIS (Section 5.3).

Check constraint: `delivery_score IN (0, 0.5, 1)`.  
Check constraint: `rating BETWEEN 1 AND 5`.

---

### `deliverables`

Proof-of-delivery assets for a booking.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `booking_id` | UUID NOT NULL FK → `bookings.id` | |
| `status` | `deliverable_status` NOT NULL DEFAULT `pending` | `pending` → `uploaded` (seller); `uploaded` → `verified` (admin, dispute contexts) |
| `file_url` | TEXT NULL | Supabase Storage URL |
| `mime_type` | TEXT NULL | Validated server-side |
| `uploaded_at` | TIMESTAMPTZ NULL | |
| `verified_at` | TIMESTAMPTZ NULL | |
| `verified_by_id` | UUID NULL FK → `users.id` | Admin |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

---

### `audit_logs`

Every admin mutation and (V1.1+) agent side-effect writes a row. No silent mutations.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `actor_id` | UUID NULL FK → `users.id` | Null for pure system/cron |
| `action` | TEXT NOT NULL | e.g. `cis_override`, `suspend_listing`, `resolve_dispute` |
| `entity_type` | TEXT NOT NULL | e.g. `listing`, `booking`, `user` |
| `entity_id` | UUID NOT NULL | |
| `details` | JSONB NOT NULL DEFAULT `{}` | Before/after payload |
| `initiated_by_agent` | BOOLEAN NOT NULL DEFAULT **false** | V1.1+ agent audit |
| `agent_session_id` | UUID NULL | Nullable; set when `initiated_by_agent` |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

---

### `buyer_agent_policies`

Spend limits for Buyer Agent bookings (Section 9.4). Checked before confirmation UI is shown.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `buyer_id` | UUID NOT NULL UNIQUE FK → `users.id` | One policy row per buyer |
| `max_per_booking_value_pence` | INTEGER NOT NULL | Cap per agent-prepared booking |
| `max_monthly_agent_spend_pence` | INTEGER NOT NULL | Monthly agent spend cap |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

---

## Relationships (summary)

```
users 1──* listings (seller_id)
users 1──* bookings (buyer_id / seller_id)
listings 1──* availability
listings 1──* bookings
bookings 1──1 reviews
bookings 1──* deliverables
users 1──1 buyer_agent_policies
users / system ──* audit_logs
```

---

## Money & CIS notes

- All monetary columns end in `_pence` and are `INTEGER`.
- `listings.cis_score` is nullable; null means "New Listing", never coerce to 0.
- Listing CIS = average of per-booking `bookings.cis_score` for `Completed` bookings, rounded to nearest integer — see `docs/cis-formula.md`.

---

## Table list

1. `users`
2. `listings`
3. `availability`
4. `bookings`
5. `reviews`
6. `deliverables`
7. `audit_logs`
8. `buyer_agent_policies`
