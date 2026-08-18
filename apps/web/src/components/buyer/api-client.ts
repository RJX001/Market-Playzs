/**
 * Buyer fetch helpers — thin wrapper around `@/lib/api`.
 */

export {
  ACCESS_TOKEN_KEY,
  ApiError,
  clearAccessToken,
  getAccessToken,
  isMissingEndpoint,
  setAccessToken,
} from "@/lib/api";

import { api, ApiError, isMissingEndpoint } from "@/lib/api";

export function getApiBase(): string {
  const raw = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  return raw.replace(/\/$/, "");
}

export function formatApiDetail(detail: unknown): string {
  if (typeof detail === "string" && detail.trim()) return detail;
  if (Array.isArray(detail)) {
    const parts = detail.map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object" && "msg" in item) {
        return String((item as { msg: unknown }).msg);
      }
      return null;
    });
    const joined = parts.filter(Boolean).join("; ");
    if (joined) return joined;
  }
  if (detail && typeof detail === "object" && "message" in detail) {
    return String((detail as { message: unknown }).message);
  }
  return "Request failed";
}

type BuyerFetchInit = RequestInit & {
  /** Attach Bearer token when present. Kept for call-site compatibility. */
  auth?: boolean;
  body?: BodyInit | object | null;
};

export async function apiFetch<T>(
  path: string,
  init: BuyerFetchInit = {},
): Promise<T> {
  const { auth: _ignoredAuth, ...rest } = init;
  void _ignoredAuth;
  return api<T>(path, rest);
}

/** Same as apiFetch but returns null on missing endpoints instead of throwing. */
export async function apiFetchOptional<T>(
  path: string,
  init: BuyerFetchInit = {},
): Promise<{ data: T; status: number } | { data: null; status: number }> {
  try {
    const data = await apiFetch<T>(path, init);
    return { data, status: 200 };
  } catch (err) {
    if (err instanceof ApiError && isMissingEndpoint(err.status)) {
      return { data: null, status: err.status };
    }
    throw err;
  }
}
