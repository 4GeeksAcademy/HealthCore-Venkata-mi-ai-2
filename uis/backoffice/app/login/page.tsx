"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { login } from "@/lib/auth-api";
import { setAuthToken } from "@/lib/auth-storage";

export default function LoginPage() {
  const searchParams = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const infoMessage =
    searchParams.get("reset") === "success"
      ? "Password reset complete. Please sign in with your new password."
      : searchParams.get("changed") === "success"
        ? "Password changed successfully."
        : null;

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await login(email, password);
      setAuthToken(result.access_token);
      window.location.href = "/";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="page-frame" style={{ maxWidth: "640px" }}>
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Authentication</p>
          <h1>Backoffice login</h1>
          <p>Sign in to access internal operations, incident analysis, and supplier tooling.</p>
        </section>

        <section className="section-card">
          <form className="stack" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>

            {infoMessage ? <p className="feedback info">{infoMessage}</p> : null}
            {error ? <p className="feedback error">{error}</p> : null}

            <div className="inline-actions">
              <button type="submit" className="button" disabled={busy}>
                {busy ? "Signing in..." : "Login"}
              </button>
              <Link href="/register" className="link-button secondary">
                Create account
              </Link>
              <Link href="/forgot-password" className="link-button secondary">
                Forgot your password?
              </Link>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
