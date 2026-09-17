"use client";

import { useEffect, useMemo } from "react";
import { usePathname, useRouter } from "next/navigation";
import { getAuthToken } from "@/lib/auth-storage";
import { isBackofficePublicPath } from "@/lib/public-routes";

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();

  const isPublicRoute = useMemo(
    () => isBackofficePublicPath(pathname),
    [pathname],
  );

  useEffect(() => {
    let cancelled = false;

    async function run() {
      const token = getAuthToken();

      if (isPublicRoute) {
        if (token && (pathname === "/login" || pathname === "/register")) {
          router.replace("/");
        }
        return;
      }

      if (!token) {
        router.replace("/login?reason=session");
        return;
      }

      try {
        const { fetchAuthMe } = await import("@/lib/auth-api");
        await fetchAuthMe();
      } catch {
        if (!cancelled) {
          router.replace("/login?reason=session");
        }
      }
    }

    void run();

    return () => {
      cancelled = true;
    };
  }, [isPublicRoute, pathname, router]);

  return <>{children}</>;
}
