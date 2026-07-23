import { buildMilestone2OpsSnapshot } from "@/lib/milestone2-metrics";

export function Milestone2OpsPanel() {
  const snapshot = buildMilestone2OpsSnapshot();

  return (
    <section className="section-card" aria-labelledby="ms2-ops-title">
      <header>
        <p className="eyebrow">Milestone 2 · src/utils</p>
        <h2 id="ms2-ops-title">Monday ops metrics (live from TypeScript utilities)</h2>
        <p>
          Visible output from HealthCore Milestone 2 Node/TypeScript logic — billing
          denials (Tom), no-show cost (Marcus), and CME risk (Diane). Source:{" "}
          <strong>{snapshot.source}</strong>. As of {snapshot.asOfDate}; no-show week
          ending {snapshot.weekEndingDate}.
        </p>
      </header>

      <div className="section-grid columns" style={{ marginTop: "1rem" }}>
        <article className="section-card">
          <h3>Billing denials</h3>
          <p style={{ fontSize: "2rem", fontWeight: 700, margin: "0.5rem 0" }}>
            {snapshot.denialRatePercent.toFixed(2)}%
          </p>
          <p>Overall denial rate across sample claims.</p>
          <ul>
            {Object.entries(snapshot.denialRateByPayer).map(([payer, rate]) => (
              <li key={payer}>
                {payer}: {rate.toFixed(2)}%
              </li>
            ))}
          </ul>
          <p>
            High-denial payers (threshold 8%):{" "}
            {snapshot.highDenialPayers.length > 0
              ? snapshot.highDenialPayers.join(", ")
              : "None"}
          </p>
        </article>

        <article className="section-card">
          <h3>No-show impact</h3>
          <p style={{ fontSize: "2rem", fontWeight: 700, margin: "0.5rem 0" }}>
            ${snapshot.miamiNoShowCostUsd.toFixed(2)}
          </p>
          <p>Estimated no-show cost — HealthCore Miami (week ending {snapshot.weekEndingDate}).</p>
          <ul>
            {Object.entries(snapshot.noShowRateByLocation).map(([locationId, rate]) => (
              <li key={locationId}>
                {locationId}: {rate.toFixed(2)}%
              </li>
            ))}
          </ul>
          <p>
            High no-show locations:{" "}
            {snapshot.highNoShowLocations.length > 0
              ? snapshot.highNoShowLocations.join(", ")
              : "None"}
          </p>
        </article>

        <article className="section-card">
          <h3>CME compliance</h3>
          <p style={{ fontSize: "2rem", fontWeight: 700, margin: "0.5rem 0" }}>
            {snapshot.cliniciansAtRiskCount}
          </p>
          <p>Clinicians at risk or overdue (as of {snapshot.asOfDate}).</p>
          <ul>
            {snapshot.cmeStatuses.map((row) => (
              <li key={row.clinicianId}>
                {row.fullName} — {row.complianceStatus} ({row.percentComplete}% complete)
              </li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}
