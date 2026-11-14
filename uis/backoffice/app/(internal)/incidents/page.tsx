import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { IncidentNav } from "@/components/incidents/IncidentNav";

export const metadata: Metadata = {
  title: "Incidents",
};

const IncidentListPanel = dynamic(
  () =>
    import("@/components/incidents/IncidentListPanel").then(
      (mod) => mod.IncidentListPanel,
    ),
  {
    loading: () => (
      <p className="muted-text" role="status">
        Loading incident list…
      </p>
    ),
  },
);

const IncidentSummaryPanel = dynamic(
  () =>
    import("@/components/incidents/IncidentSummaryPanel").then(
      (mod) => mod.IncidentSummaryPanel,
    ),
  {
    loading: () => (
      <p className="muted-text" role="status">
        Loading summary…
      </p>
    ),
  },
);

export default function IncidentsPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Incidents</p>
          <h1>Incident manager</h1>
          <p>
            Track clinic and customer incidents across the network. Register new
            reports, update lifecycle status, and review leadership summary
            totals.
          </p>
          <IncidentNav current="/incidents" />
        </section>

        <section className="section-card">
          <h2>Summary</h2>
          <IncidentSummaryPanel />
        </section>

        <IncidentListPanel />
      </div>
    </main>
  );
}
