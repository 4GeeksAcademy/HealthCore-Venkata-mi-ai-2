import { clearAuthToken, getAuthToken } from "@/lib/auth-storage";
import { messageForHttpStatus, sanitizeApiDetail } from "@/lib/user-facing-error";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_AUTH_API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_SUPPLIERS_API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_INCIDENTS_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8001"
  );
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

  const url = path.startsWith("http") ? path : `${apiBase()}${path}`;
  const headers = new Headers(init.headers ?? {});
  headers.set("Authorization", `Bearer ${token}`);

  let response: Response;
  try {
    response = await fetch(url, {
      ...init,
      headers,
    });
  } catch {
    throw new ApiError("Unable to reach the service. Please try again.", 503);
  }

  if (!response.ok) {
    const message = await parseError(response);
    if (response.status === 401) {
      handleUnauthorized();
    }
    throw new ApiError(message, response.status);
  }

  return response;
}
