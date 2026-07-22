# Marketplays — CIS Formula

Authoritative source: `docs/marketplays_cursor_rules.md` **Section 5.3**.  
Related schema: `docs/database-schema.md` (`listings.cis_score`, `bookings.cis_score`, `reviews.delivery_score` / `rating`).

CIS is **per-listing**, never per-seller.

---

## Per-booking CIS

```
delivery_component = delivery_score * 0.5     // delivery_score: 1 on-time, 0.5 late, 0 not uploaded
rating_component   = (rating / 5) * 0.5       // rating: buyer's 1–5 stars
new_booking_cis    = (delivery_component + rating_component) * 100
```

| Symbol | Source | Allowed values |
|--------|--------|----------------|
| `delivery_score` | `reviews.delivery_score` | Exactly `0`, `0.5`, or `1` |
| `rating` | `reviews.rating` | Integer 1–5 |
| `new_booking_cis` | Stored on `bookings.cis_score` when booking reaches `Completed` | 0–100 scale (float intermediate; store as integer after rounding if desired for the booking contribution — listing CIS uses AVG then round) |

On 72 hr auto-approve timeout, rating defaults to **3** (Section 5.2).

---

## Listing CIS

```
listing_cis = AVG(cis_score) across all Completed bookings for that listing,
              rounded to nearest integer
```

- Written to `listings.cis_score`.
- `listings.cis_score` is **nullable**. Null means "New" — never default to `0`.
- Admin manual edit must set `listings.is_cis_overridden = true` and write an `audit_logs` row.

---

## Recalculation triggers

Recalculate within **60 seconds** of:

1. Buyer rating submitted (`POST /api/bookings/[id]/review`)
2. 72 hr auto-approve timeout
3. Admin CIS override

---

## Example

- On-time proof (`delivery_score = 1`), rating `4`:
  - `delivery_component = 0.5`
  - `rating_component = 0.4`
  - `new_booking_cis = 90`
- Late proof (`0.5`), rating `5` → `75`
- No proof (`0`), rating `3` (auto-approve) → `30`
