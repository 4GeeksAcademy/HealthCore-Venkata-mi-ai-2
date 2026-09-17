import { Suspense } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";

export default function AuthSectionLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense
      fallback={
        <main className="app-shell">
          <div className="page-frame">
            <section className="section-card">
              <p className="muted-text" role="status">
                Loading sign-in…
              </p>
            </section>
          </div>
        </main>
      }
    >
      <AuthGuard>{children}</AuthGuard>
    </Suspense>
  );
}
