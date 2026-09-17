import Link from "next/link";
import { buildMilestone2OpsSnapshot } from "@/lib/milestone2-metrics";

export function HomeOpsSummary() {
  const snapshot = buildMilestone2OpsSnapshot();

  return (
    <section className="section-card" aria-labelledby="home-ops-title">
      <header>
        <p className="eyebrow">Operations · src/utils</p>
        <h2 id="home-ops-title">Operations snapshot</h2>
        <p>
          Live output from HealthCore operations TypeScript utilities. Source:{" "}
          <strong>{snapshot.source}</strong>. As of {snapshot.asOfDate}.
        </p>
      </header>
      <div className="section-grid columns" style={{ marginTop: "1rem" }}>
        <article className="section-card">
          <h3>Billing denials</h3>
          <p style={{ fontSize: "2rem", fontWeight: 700, margin: "0.5rem 0" }}>
            {snapshot.denialRatePercent.toFixed(2)}%
          </p>
          <p>Overall denial rate (Tom Callahan).</p>
        </article>
        <article className="section-card">
          <h3>No-show impact</h3>
          <p style={{ fontSize: "2rem", fontWeight: 700, margin: "0.5rem 0" }}>
            ${snapshot.miamiNoShowCostUsd.toFixed(2)}
          </p>
          <p>Miami week ending {snapshot.weekEndingDate} (Marcus Reid).</p>
        </article>
        <article className="section-card">
          <h3>CME compliance</h3>
          <p style={{ fontSize: "2rem", fontWeight: 700, margin: "0.5rem 0" }}>
            {snapshot.cliniciansAtRiskCount}
          </p>
          <p>Clinicians at risk or overdue (Diane Foster).</p>
        </article>
      </div>
      <p style={{ marginTop: "1rem" }}>
        <Link className="link-button secondary" href="/ops" prefetch={false}>
          Open Operations
        </Link>
      </p>
    </section>
  );
}
