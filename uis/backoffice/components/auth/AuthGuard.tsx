"use client";

import { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { fetchAuthMe } from "@/lib/auth-api";
import { getAuthToken } from "@/lib/auth-storage";

const PUBLIC_ROUTES = new Set([
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
]);

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [checkedPath, setCheckedPath] = useState<string | null>(null);

  const isPublicRoute = useMemo(() => {
    if (!pathname) return false;
    return PUBLIC_ROUTES.has(pathname);
  }, [pathname]);

  useEffect(() => {
    let cancelled = false;

    async function run() {
      const token = getAuthToken();

      if (isPublicRoute) {
        if (token && (pathname === "/login" || pathname === "/register")) {
          router.replace("/");
          return;
        }
        if (!cancelled) setCheckedPath(pathname);
        return;
      }

      if (!token) {
        router.replace("/login");
        return;
      }

      try {
        await fetchAuthMe();
        if (!cancelled) setCheckedPath(pathname);
      } catch {
        if (!cancelled) {
          router.replace("/login");
        }
      }
    }

    void run();

    return () => {
      cancelled = true;
    };
  }, [isPublicRoute, pathname, router]);

  const ready = Boolean(pathname) && checkedPath === pathname;

  if (!ready) {
    return (
      <main className="app-shell">
        <div className="page-frame">
          <section className="section-card">
            <h2>Loading session</h2>
            <p className="muted-text">Checking your backoffice authentication state.</p>
          </section>
        </div>
      </main>
    );
  }

  return <>{children}</>;
}
