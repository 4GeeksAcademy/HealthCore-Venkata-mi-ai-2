"use client";

import { useEffect, useState } from "react";
import { getAuthToken } from "@/lib/auth-storage";

/**
 * Read the backoffice JWT only after mount.
 * core-web-vitals / hydration: localStorage is unavailable on the server,
 * so the first render must match SSR (no token).
 */
export function useAuthToken(): { token: string | null; ready: boolean } {
  const [token, setToken] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setToken(getAuthToken());
    setReady(true);
  }, []);

  return { token, ready };
}
