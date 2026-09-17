"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { clearAuthToken } from "@/lib/auth-storage";
import { useAuthToken } from "@/hooks/useAuthToken";

export function SessionActions() {
  const pathname = usePathname();
  const { token, ready } = useAuthToken();

  function logout() {
    clearAuthToken();
    window.location.href = "/login";
  }

  if (!ready) {
    return (
      <div
        className="inline-actions"
        aria-hidden="true"
        style={{ minHeight: "2.25rem", minWidth: "12rem" }}
      />
    );
  }

  if (!token) {
    return (
      <div className="inline-actions">
        {pathname !== "/login" ? <Link href="/login">Login</Link> : null}
        {pathname !== "/register" ? <Link href="/register">Register</Link> : null}
      </div>
    );
  }

  return (
    <div className="inline-actions">
      <Link href="/account/profile">Profile</Link>
      <Link href="/account/change-password">Change password</Link>
      <button type="button" className="topnav-logout" onClick={logout}>
        Logout
      </button>
    </div>
  );
}
