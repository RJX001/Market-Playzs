# Buyer Map Filter Logic

Authoritative rules: `docs/marketplays_cursor_rules.md` Section 5.4.

## Composition model

Buyer map search combines filters as:

| Scope | Operator |
|-------|----------|
| Across filter **types** (location, asset type, price, CIS, …) | **AND** |
| Within a **multi-select** filter (e.g. several categories) | **OR** |

Example: `(category IN sports_club OR gym) AND (price_per_day_pence BETWEEN 500 AND 5000) AND (within radius 5km of point) AND (cis_score ≥ 70 OR cis_score IS NULL)`.

## Empty / default request

If the client sends no filters (or only empty multi-selects / unset ranges):

1. Apply **status gate** only: `status = published` (never `draft` or `suspended`).
2. Restrict to the **default viewport bounding box** (platform default, e.g. Greater London).
3. Return matching published listings — **never** an empty result set solely because filters were omitted.

## Status gate (always on for buyer queries)

Regardless of other filters or rank scores:

- **Include:** `published` listings only.
- **Exclude:** `draft` and `suspended` listings.

Seller/admin list endpoints may return drafts for the owning seller or admin tools; buyer search must not.

## Location filters

Two mutually compatible spatial modes (AND with other filter types):

### Bounding box (`bbox`)

Query params: `min_lng`, `min_lat`, `max_lng`, `max_lat`.

Listing included if `min_lng ≤ lng ≤ max_lng` AND `min_lat ≤ lat ≤ max_lat`.

### Radius (`radius`)

Query params: `center_lng`, `center_lat`, `radius_km`.

Listing included if great-circle (or PostGIS) distance from centre ≤ `radius_km`.

If both bbox and radius are provided, both must match (AND). If neither is provided on an empty filter request, use the default viewport bbox.

## Multi-select filters (OR within type)

- **Asset type / category** — values from the shared category enum (`sports_club`, `gym`, `school`, `shop`, `cafe`, `festival`, `community_event`, `billboard`, `event_venue`). Listing matches if `category` is in the selected set.
- **Audience** (when present) — OR across selected audience tags.
- **Booking type** (when present) — OR across selected booking types.

Empty multi-select = no constraint for that type (do not treat as “match nothing”).

## Range filters (AND with other types)

- **Price** — `price_min_pence` / `price_max_pence` inclusive on `price_per_day_pence` (integer pence).
- **Availability** — listing has at least one unlocked availability row in the requested date range (row-per-date model).
- **CIS score tiers** — see below.

## CIS filter behaviour

CIS is **per listing**, nullable (`null` = “New”, not zero).

When a CIS tier/min filter is applied:

- Listings whose `cis_score` falls in the requested band are included.
- Listings with **`cis_score IS NULL` are included in every CIS tier by default** and flagged “New Listing” in the UI — they are never excluded solely for having a null CIS.

To exclude New listings, the client must send an explicit `include_new_cis=false` (or equivalent) flag; default is `true`.

## Pagination & performance

- Max **20** items per response.
- Target search latency: **&lt; 300ms p95**.
- Spatial queries should use PostGIS indexes once SQLAlchemy models replace the in-memory store.

## Implementation notes

- Filter evaluation lives in the listings search service/repository — do not reimplement divergent logic in AI agent tools (Section 9: agents call the same API).
- Money comparisons use integer pence only.
