"use client";

import { FormEvent, useEffect, useState } from "react";
import { fetchAuthMe, updateProfile, type AuthMe } from "@/lib/auth-api";

export default function ProfilePage() {
  const [me, setMe] = useState<AuthMe | null>(null);
  const [name, setName] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setLoading(true);
      setError(null);
      try {
        const data = await fetchAuthMe();
        if (cancelled) return;
        setMe(data);
        setName(data.profile.name || "");
        setPhone(data.profile.phone || "");
        setAddress(data.profile.address || "");
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load profile.");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    setMessage(null);
    try {
      const updated = await updateProfile({ name, phone, address });
      if (me) {
        setMe({ ...me, profile: updated });
      }
      setMessage("Profile updated.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Profile update failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="app-shell">
      <div className="page-frame" style={{ maxWidth: "760px" }}>
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Account</p>
          <h1>My profile</h1>
          <p>Review your account identity and maintain profile contact fields.</p>
        </section>

        <section className="section-card">
          {loading ? <p className="muted-text">Loading profile...</p> : null}
          {error ? <p className="feedback error">{error}</p> : null}
          {!loading && me ? (
            <form className="stack" onSubmit={onSubmit}>
              <div className="field-grid">
                <div className="field">
                  <label htmlFor="profile-email">Email</label>
                  <input id="profile-email" value={me.email} readOnly />
                </div>
                <div className="field">
                  <label htmlFor="profile-role">Role</label>
                  <input id="profile-role" value={me.role} readOnly />
                </div>
                <div className="field">
                  <label htmlFor="profile-name">Name</label>
                  <input
                    id="profile-name"
                    value={name}
                    onChange={(e) => setName(e.target.value)}
                  />
                </div>
                <div className="field">
                  <label htmlFor="profile-phone">Phone</label>
                  <input
                    id="profile-phone"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                  />
                </div>
                <div className="field" style={{ gridColumn: "1 / -1" }}>
                  <label htmlFor="profile-address">Address</label>
                  <input
                    id="profile-address"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                  />
                </div>
              </div>
              {message ? <p className="feedback info">{message}</p> : null}
              {error ? <p className="feedback error">{error}</p> : null}
              <div className="inline-actions">
                <button type="submit" className="button" disabled={busy}>
                  {busy ? "Saving..." : "Save profile"}
                </button>
              </div>
            </form>
          ) : null}
        </section>
      </div>
    </main>
  );
}
