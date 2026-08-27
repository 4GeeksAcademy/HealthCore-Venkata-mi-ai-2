"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { forgotPassword } from "@/lib/auth-api";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [busy, setBusy] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await forgotPassword(email);
      setSubmitted(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="page-frame" style={{ maxWidth: "640px" }}>
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Authentication</p>
          <h1>Forgot password</h1>
          <p>Request a reset link for your staff account.</p>
        </section>

        <section className="section-card">
          <form className="stack" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="forgot-email">Email</label>
              <input
                id="forgot-email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={submitted || busy}
              />
            </div>

            {submitted ? (
              <p className="feedback info">
                If that address is registered, you&apos;ll receive a link shortly.
              </p>
            ) : null}
            {error ? <p className="feedback error">{error}</p> : null}

            <div className="inline-actions">
              <button type="submit" className="button" disabled={submitted || busy}>
                {busy ? "Submitting..." : "Send reset link"}
              </button>
              <Link href="/login" className="link-button secondary">
                Back to login
              </Link>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
