import { ApiError } from "@/types/api";
import { messageForHttpStatus, sanitizeApiDetail } from "@/lib/user-facing-error";

const DEFAULT_API_BASE_URL = "https://playground.4geeks.com/tracker/api/v1";

interface FetchJsonOptions extends Omit<RequestInit, "body" | "headers"> {
  body?: unknown;
  headers?: HeadersInit;
  query?: Record<string, string | undefined>;
}

function getApiBaseUrl() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();

  if (!baseUrl) {
    return `${DEFAULT_API_BASE_URL}/`;
  }

  return baseUrl.endsWith("/") ? baseUrl : `${baseUrl}/`;
}

function buildUrl(path: string, query?: Record<string, string | undefined>) {
  const normalizedPath = `/${path.replace(/^\//, "")}`;
  const params = new URLSearchParams();

  if (query) {
    Object.entries(query).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      }
    });
  }

  const queryString = params.toString();
  const baseUrl = getApiBaseUrl();

  const url = new URL(normalizedPath.replace(/^\//, ""), baseUrl);

  if (queryString) {
    url.search = queryString;
  }

  return url.toString();
}

async function parseResponse(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";

  try {
    if (contentType.includes("application/json")) {
      return await response.json();
    }
    return await response.text();
  } catch {
    throw {
      status: response.status,
      message: "Something went wrong. Please try again.",
    } satisfies ApiError;
  }
}

export async function fetchJson<T>(
  path: string,
  options: FetchJsonOptions = {},
): Promise<T> {
  const { body, headers, query, ...requestInit } = options;

  const response = await fetch(buildUrl(path, query), {
    ...requestInit,
    headers: {
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: body ? JSON.stringify(body) : undefined,
  }).catch(() => {
    throw {
      status: 503,
      message: "Unable to reach the service. Please try again.",
    } satisfies ApiError;
  });

  const payload = await parseResponse(response);

  if (!response.ok) {
    const apiError: ApiError = {
      status: response.status,
      message:
        typeof payload === "object" &&
        payload !== null &&
        "message" in payload &&
        typeof payload.message === "string"
          ? sanitizeApiDetail(response.status, payload.message)
          : messageForHttpStatus(response.status),
      details: payload,
    };

    throw apiError;
  }

  return payload as T;
}

export function getErrorMessage(error: unknown) {
  if (
    typeof error === "object" &&
    error !== null &&
    "message" in error &&
    typeof error.message === "string"
  ) {
    const status =
      "status" in error && typeof error.status === "number" ? error.status : 500;
    return sanitizeApiDetail(status, error.message);
  }

  return "Something went wrong. Please try again.";
}