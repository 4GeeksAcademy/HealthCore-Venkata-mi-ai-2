"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { login, register } from "@/lib/auth-api";
import { setAuthToken } from "@/lib/auth-storage";
import { getUserFacingError } from "@/lib/user-facing-error";

export default function RegisterPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);

    try {
      await register({ email, password, name, phone, address });
      const result = await login(email, password);
      setAuthToken(result.access_token);
      window.location.href = "/";
    } catch (err) {
      setError(getUserFacingError(err, "Unable to create the account. Please try again."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="page-frame" style={{ maxWidth: "700px" }}>
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Authentication</p>
          <h1>Create backoffice account</h1>
          <p>Register with your staff email, then continue directly into the backoffice.</p>
        </section>

        <section className="section-card">
          <form className="stack" onSubmit={onSubmit}>
            <div className="field-grid">
              <div className="field">
                <label htmlFor="register-email">Email</label>
                <input
                  id="register-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="register-password">Password</label>
                <input
                  id="register-password"
                  type="password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="register-name">Name (optional)</label>
                <input
                  id="register-name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="field">
                <label htmlFor="register-phone">Phone (optional)</label>
                <input
                  id="register-phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                />
              </div>
              <div className="field" style={{ gridColumn: "1 / -1" }}>
                <label htmlFor="register-address">Address (optional)</label>
                <input
                  id="register-address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                />
              </div>
            </div>

            {error ? (
              <div className="feedback error" role="alert">
                <p>{error}</p>
                <p>Try again, or contact HealthCore Digital support if this continues.</p>
              </div>
            ) : null}

            <div className="inline-actions">
              <button type="submit" className="button" disabled={busy}>
                {busy ? "Creating account..." : "Register"}
              </button>
              <Link href="/login" className="link-button secondary">
                Already have an account?
              </Link>
            </div>
          </form>
        </section>
      </div>
    </main>
  );
}
