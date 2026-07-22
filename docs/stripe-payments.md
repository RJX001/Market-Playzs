# Stripe Connect — Separate Charges and Transfers

Authoritative rules: `docs/marketplays_cursor_rules.md` Sections 1.1, 5.1, 5.2, 5.5.

All Stripe SDK calls live in `apps/api/app/services/stripe_service.py` only. The Stripe secret key and webhook secret are **server-side only** — never exposed to the Next.js client bundle. The frontend uses `NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY` solely to confirm PaymentIntents via Stripe.js.

## Pattern overview

Marketplays uses **Stripe Connect Separate Charges and Transfers**:

1. **Charge** the buyer on the **platform** Stripe account (`PaymentIntent`).
2. **Hold** platform funds until the booking reaches terminal success state **`Completed`**.
3. **Transfer** seller payout (less platform commission) to the seller’s **connected account** only after `Completed`.

Funds are not transferred on `Confirmed`, `Live`, or other intermediate states.

```
Buyer pays ──► PaymentIntent (platform)
                    │
                    ▼
            Pending_Payment
                    │ payment_intent.succeeded
                    ▼
               Confirmed ──► … campaign lifecycle …
                    │
                    ▼
               Completed ──► Transfer to Connect account
```

## Money units

- All amounts in the API and DB are **integer pence** (GBP minor units).
- Stripe `amount` is likewise in the smallest currency unit (pence for `gbp`).
- Format to £ only in the UI presentation layer.

## Booking creation flow (`POST /api/bookings`)

1. Validate listing is published and requested dates are available.
2. **Lock** availability rows for those dates (row-per-date).
3. Create booking in status `Pending_Payment` with `total_pence`.
4. `stripe_service.create_payment_intent(booking)` → PaymentIntent on platform account.
5. Persist `stripe_payment_intent_id` on the booking.
6. Return `{ booking_id, client_secret }` so the buyer client can confirm payment.

If payment is abandoned (~15 min) or `payment_intent.payment_failed`, transition `Pending_Payment → Cancelled` and unlock availability.

## Hold until Completed

| Event | Stripe action |
|-------|----------------|
| `payment_intent.succeeded` | Charge captured on platform; booking `Pending_Payment → Confirmed`. **No transfer yet.** |
| Booking reaches `Completed` | `stripe_service.transfer_on_completed(booking)` — Transfer to seller Connect account. |
| `Disputed → Refunded` | Full refund via Stripe Refund API; **no transfer**. |
| `Disputed → Completed` (admin approve / partial) | Transfer full or partial payout amount as resolved. |
| `Confirmed → Cancelled` (pre-start) | Refund triggered; unlock availability. |

Platform commission is deducted before transfer (`transfer_amount_pence = total_pence - commission_pence`).

## Connect onboarding (stub)

`stripe_service.create_connect_account_link(seller_id, refresh_url, return_url)` returns an Account Link URL for Express/Standard onboarding.

Publish guard (`POST /api/listings/{id}/publish`) requires the seller to have a connected Stripe account (`stripe_account_id` present and charges enabled) before a listing can go live.

## Webhook handler (`POST /api/payments/webhook`)

1. Read raw request body.
2. Validate `Stripe-Signature` header with `STRIPE_WEBHOOK_SECRET` via `stripe.Webhook.construct_event`.
3. If signature missing or invalid → **HTTP 400** (no exceptions, including preview/test).
4. Dispatch by `event.type`:
   - `payment_intent.succeeded` → booking transition to `Confirmed`.
   - `payment_intent.payment_failed` → booking transition to `Cancelled`, unlock availability.
5. Idempotent handling: ignore duplicate events for already-transitioned bookings.

Clients **never** PATCH booking `status` directly — webhooks, cron, and explicit domain actions call `booking_service.transition(...)`.

## Environment variables (API only)

```
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
STRIPE_CONNECT_CLIENT_ID=
```

Frontend publishable key only:

```
NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY=
```

## Preview vs production

- Preview deployments use Stripe **test mode** keys and a separate webhook endpoint secret.
- Production webhook URL and live keys are configured only on the production Vercel environment.
