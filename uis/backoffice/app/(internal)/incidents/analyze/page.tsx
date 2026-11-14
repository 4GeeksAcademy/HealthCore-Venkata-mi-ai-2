import type { Metadata } from "next";
import dynamic from "next/dynamic";
import { IncidentNav } from "@/components/incidents/IncidentNav";

export const metadata: Metadata = {
  title: "Incident CSV analyzer",
};

const IncidentAnalyzerPanel = dynamic(
  () =>
    import("@/components/incidents/IncidentAnalyzerPanel").then(
      (mod) => mod.IncidentAnalyzerPanel,
    ),
  {
    loading: () => (
      <p className="muted-text" role="status">
        Loading incident analyzer…
      </p>
    ),
  },
);

export default function IncidentAnalyzePage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Incidents</p>
          <h1>Incident file analyzer</h1>
          <p>
            Upload clinic incident CSVs to validate records and review category
            and status breakdowns. Analysis metrics only — registration is the
            manager entry point for new tickets.
          </p>
          <IncidentNav current="/incidents/analyze" />
        </section>
        <IncidentAnalyzerPanel />
      </div>
    </main>
  );
}
