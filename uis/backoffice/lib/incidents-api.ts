import { authedFetch } from "@/lib/authed-fetch";
import { getUserFacingError, readResponseJson } from "@/lib/user-facing-error";
import type {
  IncidentBranch,
  IncidentCategory,
  IncidentOrigin,
  IncidentStatus,
} from "@/lib/incidents-constants";

export type IncidentRecord = {
  id: string;
  title: string;
  description: string;
  category: IncidentCategory;
  status: IncidentStatus;
  origin: IncidentOrigin;
  branch: IncidentBranch;
  created_at: string;
  updated_at: string;
};

export type IncidentListResponse = {
  total: number;
  items: IncidentRecord[];
};

export type IncidentSummary = {
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_origin: Record<string, number>;
  by_branch: Record<string, number>;
  total: number;
};

export type IncidentCreateBody = {
  title: string;
  description: string;
  category: IncidentCategory;
  status: IncidentStatus;
  origin: IncidentOrigin;
  branch: IncidentBranch;
};

export type FieldApiError = {
  field?: string;
  message: string;
};

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_INCIDENTS_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8001"
  );
}

async function parseError(res: Response): Promise<FieldApiError> {
  const payload = await readResponseJson<{
    detail?: string | { field?: string; message?: string };
  }>(res).catch(() => null);
  const detail = payload?.detail;
  if (detail && typeof detail === "object") {
    return {
      field: typeof detail.field === "string" ? detail.field : undefined,
      message:
        typeof detail.message === "string"
          ? detail.message
          : "Please check the form and try again.",
    };
  }
  if (typeof detail === "string") {
    return { message: getUserFacingError({ status: res.status, message: detail }, "Please try again.") };
  }
  return {
    message: getUserFacingError(
      { status: res.status, message: undefined },
      "Something went wrong. Please try again.",
    ),
  };
}

export async function createIncident(
  body: IncidentCreateBody,
): Promise<IncidentRecord> {
  const res = await authedFetch(`${apiBase()}/api/incidents`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await parseError(res);
    const error = new Error(err.message) as Error & FieldApiError;
    error.field = err.field;
    error.message = err.message;
    throw error;
  }
  return readResponseJson<IncidentRecord>(res);
}

export async function fetchIncidents(params: {
  status?: string;
  origin?: string;
  branch?: string;
  category?: string;
}): Promise<IncidentListResponse> {
  const query = new URLSearchParams();
  if (params.status) query.set("status", params.status);
  if (params.origin) query.set("origin", params.origin);
  if (params.branch) query.set("branch", params.branch);
  if (params.category) query.set("category", params.category);
  query.set("limit", "200");
  const suffix = query.toString() ? `?${query}` : "";
  const res = await authedFetch(`${apiBase()}/api/incidents${suffix}`);
  if (!res.ok) {
    const err = await parseError(res);
    throw new Error(err.message);
  }
  return readResponseJson<IncidentListResponse>(res);
}

export async function fetchIncidentSummary(): Promise<IncidentSummary> {
  const res = await authedFetch(`${apiBase()}/api/incidents/summary`);
  if (!res.ok) {
    const err = await parseError(res);
    throw new Error(err.message);
  }
  return readResponseJson<IncidentSummary>(res);
}

export async function patchIncidentStatus(
  id: string,
  status: IncidentStatus,
): Promise<IncidentRecord> {
  const res = await authedFetch(`${apiBase()}/api/incidents/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    const err = await parseError(res);
    throw new Error(err.message);
  }
  return readResponseJson<IncidentRecord>(res);
}
