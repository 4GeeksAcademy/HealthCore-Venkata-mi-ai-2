import type { Metadata } from "next";
import { Suspense } from "react";
import { LoginForm } from "@/components/auth/LoginForm";

export const metadata: Metadata = {
  title: "Login",
};

export default function LoginPage() {
  return (
    <main className="app-shell">
      <div className="page-frame" style={{ maxWidth: "640px" }}>
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Authentication</p>
          <h1>Backoffice login</h1>
          <p>
            Sign in to access internal operations, incident analysis, and supplier
            tooling.
          </p>
        </section>
        <Suspense
          fallback={
            <section className="section-card">
              <p className="muted-text" role="status">
                Loading sign-in…
              </p>
            </section>
          }
        >
          <LoginForm />
        </Suspense>
      </div>
    </main>
  );
}
