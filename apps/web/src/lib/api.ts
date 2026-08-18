/**
 * Shared MarketPlays API client.
 *
 * Portal modules should import this (or a thin wrapper that re-exports it).
 * Access JWT is read from localStorage key `mp_access_token`.
 */

const DEFAULT_API_URL = "http://localhost:8000";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || DEFAULT_API_URL;

export const ACCESS_TOKEN_KEY = "mp_access_token";

export class ApiError extends Error {
  readonly status: number;
  readonly detail: unknown;

  constructor(message: string, status: number, detail: unknown = null) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.detail = detail;
  }
}

export function getAccessToken(): string | null {
  if (typeof window === "undefined") {
    return null;
  }
  try {
    return window.localStorage.getItem(ACCESS_TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setAccessToken(token: string): void {
  if (typeof window === "undefined") return;
  window.localStorage.setItem(ACCESS_TOKEN_KEY, token);
}

export function clearAccessToken(): void {
  if (typeof window === "undefined") return;
  window.localStorage.removeItem(ACCESS_TOKEN_KEY);
}

export function isMissingEndpoint(status: number): boolean {
  return status === 404 || status === 405 || status === 501;
}

function formatDetail(detail: unknown): string | null {
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
  return null;
}

function resolveUrl(path: string): string {
  if (path.startsWith("http://") || path.startsWith("https://")) {
    return path;
  }
  const normalized = path.startsWith("/") ? path : `/${path}`;
  return `${API_BASE_URL}${normalized}`;
}

function isRawBody(body: unknown): body is BodyInit {
  return (
    typeof body === "string" ||
    body instanceof FormData ||
    body instanceof Blob ||
    body instanceof URLSearchParams ||
    body instanceof ArrayBuffer ||
    ArrayBuffer.isView(body)
  );
}

export type ApiInit = Omit<RequestInit, "body"> & {
  body?: BodyInit | object | null;
};

export async function api<T = unknown>(
  path: string,
  init: ApiInit = {},
): Promise<T> {
  const { body, headers: initHeaders, ...rest } = init;
  const headers = new Headers(initHeaders);

  let payload: BodyInit | null | undefined;
  if (body === undefined || body === null) {
    payload = body as null | undefined;
  } else if (isRawBody(body)) {
    payload = body;
  } else {
    if (!headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    payload = JSON.stringify(body);
  }

  const token = getAccessToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }

  if (payload instanceof FormData) {
    headers.delete("Content-Type");
  }

  let response: Response;
  try {
    response = await fetch(resolveUrl(path), {
      ...rest,
      headers,
      body: payload,
      credentials: "include",
    });
  } catch {
    throw new ApiError("Network error — could not reach the API.", 0, null);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type") ?? "";
  const isJson = contentType.includes("application/json");
  const data: unknown = isJson
    ? await response.json().catch(() => null)
    : await response.text();

  if (!response.ok) {
    const detail =
      data && typeof data === "object" && "detail" in data
        ? (data as { detail: unknown }).detail
        : data;
    const message =
      formatDetail(detail) || `Request failed (${response.status})`;
    throw new ApiError(message, response.status, detail);
  }

  if (!isJson) {
    return data as T;
  }

  return data as T;
}

export function apiGet<T>(path: string, init?: ApiInit): Promise<T> {
  return api<T>(path, { ...init, method: "GET" });
}

export function apiPost<T>(
  path: string,
  body?: ApiInit["body"],
  init?: ApiInit,
): Promise<T> {
  return api<T>(path, { ...init, method: "POST", body });
}

export function apiPatch<T>(
  path: string,
  body?: ApiInit["body"],
  init?: ApiInit,
): Promise<T> {
  return api<T>(path, { ...init, method: "PATCH", body });
}

export function apiDelete<T>(path: string, init?: ApiInit): Promise<T> {
  return api<T>(path, { ...init, method: "DELETE" });
}
