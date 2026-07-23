import { ApiError } from "@/types/api";

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

  if (contentType.includes("application/json")) {
    return response.json();
  }

  return response.text();
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
          ? payload.message
          : `Request failed with status ${response.status}.`,
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
    return error.message;
  }

  return "An unexpected error occurred.";
}