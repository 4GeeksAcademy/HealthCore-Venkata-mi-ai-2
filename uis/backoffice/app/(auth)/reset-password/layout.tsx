import { Suspense } from "react";

export default function ResetPasswordLayout({
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
                Loading password reset…
              </p>
            </section>
          </div>
        </main>
      }
    >
      {children}
    </Suspense>
  );
}
