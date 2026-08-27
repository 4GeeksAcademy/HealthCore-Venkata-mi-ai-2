import { clearAuthToken, getAuthToken } from "@/lib/auth-storage";

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
    if (typeof payload.detail === "string") return payload.detail;
    if (Array.isArray(payload.detail)) {
      return payload.detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join("; ");
    }
  } catch {
    // ignore parse errors and use status fallback
  }
  return `Request failed (${res.status})`;
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

  const response = await fetch(url, {
    ...init,
    headers,
  });

  if (!response.ok) {
    const message = await parseError(response);
    if (response.status === 401) {
      handleUnauthorized();
    }
    throw new ApiError(message, response.status);
  }

  return response;
}
