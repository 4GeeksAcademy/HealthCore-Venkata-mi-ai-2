import type { Metadata } from "next";
import Link from "next/link";
import { IncidentAnalyzerPanel } from "@/components/incidents/IncidentAnalyzerPanel";

export const metadata: Metadata = {
  title: "Incident analysis",
};

export default function IncidentsPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Incidents</p>
          <h1>Incident file analyzer</h1>
          <p>
            Upload clinic incident CSVs to validate records, review category and
            status breakdowns, and export metric results. Logic matches{" "}
            <code>docs/Project_Contexts/IncidentFileAnalyzer.md</code>.
          </p>
          <div className="inline-actions">
            <Link className="link-button secondary" href="/">
              Back to welcome
            </Link>
          </div>
        </section>

        <IncidentAnalyzerPanel />
      </div>
    </main>
  );
}
