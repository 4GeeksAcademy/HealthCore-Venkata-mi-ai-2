import { buildMilestone2OpsSnapshot } from "@/lib/milestone2-metrics";

export function Milestone2OpsPanel() {
  const snapshot = buildMilestone2OpsSnapshot();

  return (
    <section className="section-card" aria-labelledby="ms2-ops-title">
      <header>
        <p className="eyebrow">Operations · src/utils</p>
        <h2 id="ms2-ops-title">Operations metrics (live from TypeScript utilities)</h2>
        <p>
          Visible output from HealthCore operations TypeScript logic — billing
          denials (Tom), no-show cost (Marcus), and CME risk (Diane). Source:{" "}
          <strong>{snapshot.source}</strong>. As of {snapshot.asOfDate}; no-show week
          ending {snapshot.weekEndingDate}.
        </p>
      </header>

      <div className="section-grid columns" style={{ marginTop: "1rem" }}>
        <article className="section-card ops-metric-card">
          <h3>Billing denials</h3>
          <p className="ops-metric-value">{snapshot.denialRatePercent.toFixed(2)}%</p>
          <p>Overall denial rate across sample claims.</p>
          <p>
            High-denial payers (threshold 8%):{" "}
            {snapshot.highDenialPayers.length > 0
              ? snapshot.highDenialPayers.join(", ")
              : "None"}
          </p>
          <details>
            <summary>Denial rate by payer</summary>
            <ul>
              {Object.entries(snapshot.denialRateByPayer).map(([payer, rate]) => (
                <li key={payer}>
                  {payer}: {rate.toFixed(2)}%
                </li>
              ))}
            </ul>
          </details>
        </article>

        <article className="section-card ops-metric-card">
          <h3>No-show impact</h3>
          <p className="ops-metric-value">${snapshot.miamiNoShowCostUsd.toFixed(2)}</p>
          <p>Estimated no-show cost — HealthCore Miami (week ending {snapshot.weekEndingDate}).</p>
          <p>
            High no-show locations:{" "}
            {snapshot.highNoShowLocations.length > 0
              ? snapshot.highNoShowLocations.join(", ")
              : "None"}
          </p>
          <details>
            <summary>No-show rate by location</summary>
            <ul>
              {Object.entries(snapshot.noShowRateByLocation).map(([locationId, rate]) => (
                <li key={locationId}>
                  {locationId}: {rate.toFixed(2)}%
                </li>
              ))}
            </ul>
          </details>
        </article>

        <article className="section-card ops-metric-card">
          <h3>CME compliance</h3>
          <p className="ops-metric-value">{snapshot.cliniciansAtRiskCount}</p>
          <p>Clinicians at risk or overdue (as of {snapshot.asOfDate}).</p>
          <details>
            <summary>Clinician CME status</summary>
            <ul>
              {snapshot.cmeStatuses.map((row) => (
                <li key={row.clinicianId}>
                  {row.fullName} — {row.complianceStatus} ({row.percentComplete}% complete)
                </li>
              ))}
            </ul>
          </details>
        </article>
      </div>
    </section>
  );
}
