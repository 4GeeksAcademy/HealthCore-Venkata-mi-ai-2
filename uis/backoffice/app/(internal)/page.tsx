import Link from "next/link";
import { HomeOpsSummary } from "@/components/ops/HomeOpsSummary";
import { branding } from "@/lib/branding";

export default function BackofficeWelcomePage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Internal</p>
          <h1>Welcome to the HealthCore backoffice</h1>
          <p>
            Secure internal workspace for clinic operations and people teams.
            This layout is independent of the public HealthCore website.
          </p>
        </section>

        <section className="section-card">
          <h2>Available modules</h2>
          <p>
            Monday operations metrics use TypeScript utilities from <code>src/utils</code>.
            Hiring support remains available for Diane Foster&apos;s pipeline.
          </p>
          <div className="inline-actions" style={{ marginTop: "1rem" }}>
            <Link className="link-button" href="/ops" prefetch={false}>
              Open Operations
            </Link>
            <Link className="link-button secondary" href="/incidents" prefetch={false}>
              Open incident analysis
            </Link>
            <Link className="link-button secondary" href="/suppliers" prefetch={false}>
              Open supplier directory
            </Link>
            <Link className="link-button secondary" href="/inventory" prefetch={false}>
              Open clinic inventory
            </Link>
            <Link className="link-button secondary" href="/hiring" prefetch={false}>
              Open {branding.appName}
            </Link>
          </div>
        </section>

        <HomeOpsSummary />

        <section className="section-card">
          <h2>Who this serves</h2>
          <ul>
            <li>James Osei — CTO, HealthCore Digital</li>
            <li>Diane Foster — People & workforce hiring</li>
            <li>Tom Callahan — Billing denial operations</li>
            <li>Marcus Reid — Clinical no-show impact</li>
          </ul>
        </section>
      </div>
    </main>
  );
}
