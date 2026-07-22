/**
 * Admin API stubs — frontend only.
 * TODO: wire to real FastAPI admin endpoints once backend is available.
 */

export type DisputeResolutionAction =
  | "approve_seller"
  | "full_refund"
  | "partial_refund";

export interface ResolveDisputePayload {
  disputeId: string;
  action: DisputeResolutionAction;
  /** Required when action is partial_refund — integer percent 1–99 */
  refundPercent?: number;
}

export interface SuspendUserPayload {
  userId: string;
  reason: string;
}

export interface CisOverridePayload {
  listingId: string;
  cisScore: number;
}

export interface SuspendListingPayload {
  listingId: string;
  reason: string;
}

async function adminFetch(
  path: string,
  init?: RequestInit,
): Promise<{ ok: boolean; stub: true; path: string }> {
  // TODO: replace with real fetch to NEXT_PUBLIC_API_URL + path
  // await fetch(`${process.env.NEXT_PUBLIC_API_URL}${path}`, {
  //   ...init,
  //   headers: { Authorization: `Bearer ${token}`, ...init?.headers },
  // });
  void init;
  console.info(`[admin stub] POST ${path}`, init?.body);
  return { ok: true, stub: true, path };
}

/** POST /api/admin/disputes/{id}/resolve — writes audit_logs row server-side */
export async function resolveDispute(
  payload: ResolveDisputePayload,
): Promise<{ ok: boolean; stub: true; path: string }> {
  return adminFetch(`/api/admin/disputes/${payload.disputeId}/resolve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      action: payload.action,
      refund_percent: payload.refundPercent,
    }),
  });
}

/** POST /api/admin/users/{id}/suspend — writes audit_logs row server-side */
export async function suspendUser(
  payload: SuspendUserPayload,
): Promise<{ ok: boolean; stub: true; path: string }> {
  return adminFetch(`/api/admin/users/${payload.userId}/suspend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: payload.reason }),
  });
}

/**
 * POST /api/admin/listings/{id}/cis-override
 * Sets is_cis_overridden = true and writes audit_logs row server-side.
 */
export async function overrideCis(
  payload: CisOverridePayload,
): Promise<{ ok: boolean; stub: true; path: string }> {
  return adminFetch(`/api/admin/listings/${payload.listingId}/cis-override`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ cis_score: payload.cisScore }),
  });
}

/** POST /api/admin/listings/{id}/suspend — writes audit_logs row server-side */
export async function suspendListing(
  payload: SuspendListingPayload,
): Promise<{ ok: boolean; stub: true; path: string }> {
  return adminFetch(`/api/admin/listings/${payload.listingId}/suspend`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason: payload.reason }),
  });
}
