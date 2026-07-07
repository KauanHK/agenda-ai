// Tiny fetch-based HTTP client with bearer auth + auto refresh.
//
// - Reads VITE_API_URL from import.meta.env.
// - Persists tokens in localStorage.
// - Queues requests during a refresh and retries them once the new
//   access token is available.

import type { TokenResponse } from "./types";

const API_URL = (import.meta.env.VITE_API_URL ?? "").replace(/\/+$/, "");
const STORAGE_KEY = "agenda.auth";

interface PersistedAuth {
  access_token: string;
  refresh_token: string;
}

let memoryAuth: PersistedAuth | null = null;
const authListeners = new Set<(a: PersistedAuth | null) => void>();

function loadAuth(): PersistedAuth | null {
  if (memoryAuth) return memoryAuth;
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    memoryAuth = JSON.parse(raw) as PersistedAuth;
    return memoryAuth;
  } catch {
    return null;
  }
}

export function setAuth(tokens: TokenResponse | null) {
  if (tokens) {
    memoryAuth = { access_token: tokens.access_token, refresh_token: tokens.refresh_token };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(memoryAuth));
  } else {
    memoryAuth = null;
    localStorage.removeItem(STORAGE_KEY);
  }
  authListeners.forEach((fn) => fn(memoryAuth));
}

export function getAuth(): PersistedAuth | null {
  return loadAuth();
}

export function subscribeAuth(fn: (a: PersistedAuth | null) => void) {
  authListeners.add(fn);
  return () => authListeners.delete(fn);
}

export class ApiError extends Error {
  status: number;
  detail: unknown;
  constructor(status: number, message: string, detail?: unknown) {
    super(message);
    this.status = status;
    this.detail = detail;
  }
}

interface RequestOptions {
  method?: "GET" | "POST" | "PUT" | "PATCH" | "DELETE";
  body?: unknown;
  /** Send as application/x-www-form-urlencoded instead of JSON. */
  formBody?: Record<string, string>;
  query?: Record<string, string | number | boolean | null | undefined>;
  auth?: boolean;
  signal?: AbortSignal;
}

let refreshPromise: Promise<PersistedAuth | null> | null = null;

async function refreshTokens(): Promise<PersistedAuth | null> {
  const current = getAuth();
  if (!current) return null;

  if (!refreshPromise) {
    refreshPromise = (async () => {
      try {
        const res = await fetch(`${API_URL}/auth/refresh`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ refresh_token: current.refresh_token }),
        });
        if (!res.ok) throw new Error("refresh failed");
        const tokens = (await res.json()) as TokenResponse;
        setAuth(tokens);
        return getAuth();
      } catch {
        setAuth(null);
        return null;
      } finally {
        refreshPromise = null;
      }
    })();
  }
  return refreshPromise;
}

function buildUrl(path: string, query?: RequestOptions["query"]) {
  let url = `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
  if (query) {
    const params = new URLSearchParams();
    for (const [k, v] of Object.entries(query)) {
      if (v === null || v === undefined || v === "") continue;
      params.append(k, String(v));
    }
    const qs = params.toString();
    if (qs) url += `?${qs}`;
  }
  return url;
}

export async function request<T>(path: string, opts: RequestOptions = {}): Promise<T> {
  const method = opts.method ?? "GET";
  const useAuth = opts.auth !== false;

  const serializedBody = opts.body !== undefined ? JSON.stringify(opts.body) : undefined;
  const formBody = opts.formBody !== undefined ? new URLSearchParams(opts.formBody).toString() : undefined;

  const doFetch = async (token: string | null): Promise<Response> => {
    const headers: Record<string, string> = {};
    if (formBody !== undefined) headers["Content-Type"] = "application/x-www-form-urlencoded";
    else if (serializedBody !== undefined) headers["Content-Type"] = "application/json";
    if (useAuth && token) headers["Authorization"] = `Bearer ${token}`;

    const rawBody = formBody ?? serializedBody;

    let res = await fetch(buildUrl(path, opts.query), {
      method,
      headers,
      body: rawBody,
      signal: opts.signal,
      redirect: "manual",
    });

    // Follow 307/308 manually to preserve method, body and Authorization header.
    while (res.status === 307 || res.status === 308) {
      const location = res.headers.get("Location");
      if (!location) break;
      res = await fetch(location, {
        method,
        headers,
        body: rawBody,
        signal: opts.signal,
        redirect: "manual",
      });
    }

    return res;
  };

  let auth = useAuth ? getAuth() : null;
  let res = await doFetch(auth?.access_token ?? null);

  if (res.status === 401 && useAuth && auth) {
    auth = await refreshTokens();
    if (!auth) {
      throw new ApiError(401, "Sessão expirada");
    }
    res = await doFetch(auth.access_token);
  }

  if (res.status === 204) return undefined as T;

  let payload: unknown = null;
  const text = await res.text();
  if (text) {
    try { payload = JSON.parse(text); } catch { payload = text; }
  }

  if (!res.ok) {
    const detail = (payload as any)?.detail ?? payload;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((d: any) => d?.msg).filter(Boolean).join(", ") || res.statusText
          : (detail as any)?.msg ?? res.statusText ?? `HTTP ${res.status}`;
    throw new ApiError(res.status, message, detail);
  }

  return payload as T;
}

export const api = {
  get: <T>(path: string, query?: RequestOptions["query"], opts: Omit<RequestOptions, "method" | "body" | "query"> = {}) =>
    request<T>(path, { ...opts, method: "GET", query }),
  post: <T>(path: string, body?: unknown, opts: Omit<RequestOptions, "method" | "body"> = {}) =>
    request<T>(path, { ...opts, method: "POST", body }),
  put: <T>(path: string, body?: unknown, opts: Omit<RequestOptions, "method" | "body"> = {}) =>
    request<T>(path, { ...opts, method: "PUT", body }),
  patch: <T>(path: string, body?: unknown, opts: Omit<RequestOptions, "method" | "body"> = {}) =>
    request<T>(path, { ...opts, method: "PATCH", body }),
  delete: <T>(path: string, opts: Omit<RequestOptions, "method" | "body"> = {}) =>
    request<T>(path, { ...opts, method: "DELETE" }),
};
