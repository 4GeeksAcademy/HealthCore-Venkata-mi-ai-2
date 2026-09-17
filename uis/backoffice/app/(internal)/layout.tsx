import Link from "next/link";
import { Suspense } from "react";
import { AuthGuard } from "@/components/auth/AuthGuard";
import { SessionActions } from "@/components/auth/SessionActions";
import { branding } from "@/lib/branding";

export default function InternalLayout({
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
                Loading backoffice…
              </p>
            </section>
          </div>
        </main>
      }
    >
      <AuthGuard>
        <div className="backoffice-topnav">
          <div className="backoffice-topnav-inner">
            <Link href="/" className="backoffice-brand" prefetch={false}>
              {branding.companyName} Backoffice
            </Link>
            <nav aria-label="Backoffice">
              <Link href="/" prefetch={false}>
                Home
              </Link>
              <Link href="/ops" prefetch={false}>
                Operations
              </Link>
              <Link href="/incidents" prefetch={false}>
                Incident analysis
              </Link>
              <Link href="/suppliers" prefetch={false}>
                Suppliers
              </Link>
              <Link href="/inventory" prefetch={false}>
                Inventory
              </Link>
              <Link href="/hiring" prefetch={false}>
                Hiring tracker
              </Link>
            </nav>
            <SessionActions />
          </div>
        </div>
        {children}
      </AuthGuard>
    </Suspense>
  );
}
