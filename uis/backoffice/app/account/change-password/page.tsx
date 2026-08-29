"use client";

import { FormEvent, useState } from "react";
import { changePassword } from "@/lib/auth-api";
import { getUserFacingError } from "@/lib/user-facing-error";

export default function ChangePasswordPage() {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setMessage(null);
    setError(null);

    if (newPassword !== confirmPassword) {
      setError("New password and confirmation must match.");
      return;
    }

    setBusy(true);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setMessage("Password updated successfully.");
    } catch (err) {
      setError(
        getUserFacingError(err, "Unable to change the password. Please try again."),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="page-frame" style={{ maxWidth: "640px" }}>
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Account</p>
          <h1>Change password</h1>
          <p>Update your password while signed in.</p>
        </section>

        <section className="section-card">
          <form className="stack" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="current-password">Current password</label>
              <input
                id="current-password"
                type="password"
                required
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
            </div>
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
            {message ? <p className="feedback info">{message}</p> : null}
            {error ? (
              <div className="feedback error" role="alert">
                <p>{error}</p>
                <p>Try again, or contact HealthCore Digital support if this continues.</p>
              </div>
            ) : null}
            <div className="inline-actions">
              <button type="submit" className="button" disabled={busy}>
                {busy ? "Updating..." : "Change password"}
              </button>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
