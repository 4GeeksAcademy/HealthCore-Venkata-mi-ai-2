import { Suspense } from "react";

export default function LoginLayout({
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
      {children}
    </Suspense>
  );
}
