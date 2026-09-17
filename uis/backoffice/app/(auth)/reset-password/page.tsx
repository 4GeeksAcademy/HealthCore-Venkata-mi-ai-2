"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { FormEvent, useState } from "react";
import { resetPassword } from "@/lib/auth-api";
import { getUserFacingError } from "@/lib/user-facing-error";

export default function ResetPasswordPage() {
  const searchParams = useSearchParams();
  const token = searchParams.get("token") ?? "";

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);

    if (!token) {
      setError("Reset token is missing. Request a new password reset email.");
      return;
    }

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation must match.");
      return;
    }

    setBusy(true);
    try {
      await resetPassword(token, newPassword);
      window.location.href = "/login?reset=success";
    } catch (err) {
      setError(
        getUserFacingError(
          err,
          "Unable to reset the password. Request a new link and try again.",
        ),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="page-frame" style={{ maxWidth: "640px" }}>
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Authentication</p>
          <h1>Reset password</h1>
          <p>Set a new password for your account using the email reset link token.</p>
        </section>

        <section className="section-card">
          <form className="stack" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="new-password">New password</label>
              <input
                id="new-password"
                type="password"
                required
                minLength={8}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
            </div>
            <div className="field">
              <label htmlFor="confirm-password">Confirm new password</label>
              <input
                id="confirm-password"
                type="password"
                required
                minLength={8}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
              />
            </div>

            {error ? (
              <div className="feedback error">
                <p>{error}</p>
                <p>
                  Request a fresh link from <Link href="/forgot-password">forgot password</Link>.
                </p>
              </div>
            ) : null}

            <div className="inline-actions">
              <button type="submit" className="button" disabled={busy}>
                {busy ? "Updating..." : "Reset password"}
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
