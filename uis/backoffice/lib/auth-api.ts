import { authedFetch } from "@/lib/authed-fetch";
import {
  messageForHttpStatus,
  readResponseJson,
  sanitizeApiDetail,
} from "@/lib/user-facing-error";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_AUTH_API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_SUPPLIERS_API_URL?.replace(/\/$/, "") ||
    process.env.NEXT_PUBLIC_INCIDENTS_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8001"
  );
}

async function parseError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as {
      detail?: string | Array<{ msg?: string }>;
    };
    if (typeof body.detail === "string") {
      return sanitizeApiDetail(res.status, body.detail);
    }
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      return messageForHttpStatus(res.status);
    }
  } catch {
    // Use a status-based message instead of parse or status-code text.
  }
  return messageForHttpStatus(res.status);
}

export type RegisterPayload = {
  email: string;
  password: string;
  name?: string;
  phone?: string;
  address?: string;
};

export type AuthTokenResponse = {
  access_token: string;
  token_type: "bearer";
};

export type Profile = {
  id: number;
  user_id: number;
  name: string;
  phone: string;
  address: string;
};

export type AuthMe = {
  id: number;
  email: string;
  role: "admin" | "manager" | "user";
  is_active: boolean;
  profile: Profile;
};

async function publicFetch(path: string, init: RequestInit): Promise<Response> {
  let res: Response;
  try {
    res = await fetch(`${apiBase()}${path}`, init);
  } catch {
    throw new Error("Unable to reach the service. Please try again.");
  }
  if (!res.ok) throw new Error(await parseError(res));
  return res;
}

export async function login(email: string, password: string): Promise<AuthTokenResponse> {
  const res = await publicFetch("/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  return readResponseJson<AuthTokenResponse>(res);
}

export async function register(payload: RegisterPayload): Promise<void> {
  await publicFetch("/users", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
}

export async function fetchAuthMe(): Promise<AuthMe> {
  const res = await authedFetch("/auth/me", {
    cache: "no-store",
  });
  return readResponseJson<AuthMe>(res);
}

export async function updateProfile(payload: {
  name?: string;
  phone?: string;
  address?: string;
}): Promise<Profile> {
  const res = await authedFetch("/profiles/me", {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readResponseJson<Profile>(res);
}

export async function forgotPassword(email: string): Promise<void> {
  await publicFetch("/auth/forgot-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  await publicFetch("/auth/reset-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
}

export async function changePassword(currentPassword: string, newPassword: string): Promise<void> {
  await authedFetch("/auth/change-password", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}
