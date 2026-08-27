import { authedFetch } from "@/lib/authed-fetch";

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
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join("; ");
    }
  } catch {
    // ignore
  }
  return `Request failed (${res.status})`;
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

export async function login(email: string, password: string): Promise<AuthTokenResponse> {
  const res = await fetch(`${apiBase()}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  return (await res.json()) as AuthTokenResponse;
}

export async function register(payload: RegisterPayload): Promise<void> {
  const res = await fetch(`${apiBase()}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export async function fetchAuthMe(): Promise<AuthMe> {
  const res = await authedFetch("/auth/me", {
    cache: "no-store",
  });
  return (await res.json()) as AuthMe;
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
  return (await res.json()) as Profile;
}

export async function forgotPassword(email: string): Promise<void> {
  const res = await fetch(`${apiBase()}/auth/forgot-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw new Error(await parseError(res));
}

export async function resetPassword(token: string, newPassword: string): Promise<void> {
  const res = await fetch(`${apiBase()}/auth/reset-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, new_password: newPassword }),
  });
  if (!res.ok) throw new Error(await parseError(res));
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
