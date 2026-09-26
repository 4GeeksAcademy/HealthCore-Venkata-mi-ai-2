import { clearAuthToken, getAuthToken } from "@/lib/auth-storage";
import { routeTemplate, track } from "@/lib/telemetry";
import { messageForHttpStatus, sanitizeApiDetail } from "@/lib/user-facing-error";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_AUTH_API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_SUPPLIERS_API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_INCIDENTS_API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_INVENTORY_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8001"
  );
}

export function resolveApiUrl(path: string, base: string = apiBase()): string {
  if (/^https?:\/\//i.test(path)) {
    return path;
  }
  const normalizedBase = base.replace(/\/$/, "");
  if (path === normalizedBase || path.startsWith(`${normalizedBase}/`)) {
    return path;
  }
  const suffix = path.startsWith("/") ? path : `/${path}`;
  return `${normalizedBase}${suffix}`;
}

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

async function parseError(res: Response): Promise<string> {
  try {
    const payload = (await res.json()) as {
      detail?: string | Array<{ msg?: string }>;
    };
    if (typeof payload.detail === "string") {
      return sanitizeApiDetail(res.status, payload.detail);
    }
    if (Array.isArray(payload.detail) && payload.detail.length > 0) {
      return messageForHttpStatus(res.status);
    }
  } catch {
    // Use a status-based message instead of parse or status-code text.
  }
  return messageForHttpStatus(res.status);
}

function handleUnauthorized(): void {
  clearAuthToken();
  if (typeof window !== "undefined") {
    const currentPath = window.location.pathname;
    if (currentPath !== "/login") {
      window.location.href = "/login";
    }
  }
}

export async function authedFetch(
  path: string,
  init: RequestInit = {},
): Promise<Response> {
  const token = getAuthToken();
  if (!token) {
    handleUnauthorized();
    throw new ApiError("Authentication required", 401);
  }

  const url = resolveApiUrl(path);
  const headers = new Headers(init.headers ?? {});
  headers.set("Authorization", `Bearer ${token}`);
  const method = (init.method ?? "GET").toUpperCase();
  const started = performance.now();

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers,
    });
  } catch {
    const template = routeTemplate(url);
    track("api_request_failed", {
      method,
      route_template: template,
      status_code: 503,
    });
    throw new ApiError("Unable to reach the service. Please try again.", 503);
  }

  recordApiTiming(method, url, response, performance.now() - started);

  if (!response.ok) {
    const message = await parseError(response);
    if (response.status === 401) {
      track("session_expired", { reason: tokenExpiryReason(token) });
      handleUnauthorized();
    }
    throw new ApiError(message, response.status);
  }

  return response;
}

function tokenExpiryReason(token: string): "token_expired" | "token_invalid" {
  const part = token.split(".")[1];
  if (!part) return "token_invalid";
  try {
    const json = JSON.parse(atob(part.replace(/-/g, "+").replace(/_/g, "/"))) as {
      exp?: unknown;
    };
    if (typeof json.exp === "number" && json.exp * 1000 <= Date.now()) {
      return "token_expired";
    }
  } catch {
    return "token_invalid";
  }
  return "token_invalid";
}

function recordApiTiming(method: string, url: string, response: Response, durationMs: number): void {
  const template = routeTemplate(url);
  if (template.startsWith("/telemetry")) return;
  const cacheHeader = response.headers.get("X-Cache");
  const cacheStatus = cacheHeader === "HIT" || cacheHeader === "MISS" ? cacheHeader : "NONE";
  track("api_latency_recorded", {
    method,
    route_template: template,
    status_code: response.status,
    duration_ms: durationMs,
    cache_status: cacheStatus,
  });
  if (response.status === 500 || response.status === 503) {
    track("api_request_failed", {
      method,
      route_template: template,
      status_code: response.status,
    });
  }
}
