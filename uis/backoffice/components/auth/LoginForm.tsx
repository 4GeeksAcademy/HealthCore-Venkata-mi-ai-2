"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { login } from "@/lib/auth-api";
import { setAuthToken } from "@/lib/auth-storage";
import { getUserFacingError } from "@/lib/user-facing-error";

export function LoginForm() {
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
        : searchParams.get("reason") === "session"
          ? "Your session expired or could not be verified. Please sign in again."
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
      setError(getUserFacingError(err, "Unable to sign in. Please try again."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="section-card">
      <form className="stack" onSubmit={onSubmit}>
        <div className="field">
          <label htmlFor="login-email">Email</label>
          <input
            id="login-email"
            type="email"
            autoComplete="username"
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
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>

        {infoMessage ? <p className="feedback info">{infoMessage}</p> : null}
        {error ? (
          <div className="feedback error" role="alert">
            <p>{error}</p>
            <p>Try again, or contact HealthCore Digital support if this continues.</p>
          </div>
        ) : null}

        <div className="inline-actions">
          <button type="submit" className="button" disabled={busy}>
            {busy ? "Signing in..." : "Login"}
          </button>
          <Link href="/register" className="link-button secondary" prefetch={false}>
            Create account
          </Link>
          <Link href="/forgot-password" className="link-button secondary" prefetch={false}>
            Forgot your password?
          </Link>
        </div>
      </form>
    </section>
  );
}
