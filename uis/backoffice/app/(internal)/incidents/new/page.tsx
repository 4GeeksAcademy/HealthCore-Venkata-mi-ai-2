import type { Metadata } from "next";
import { IncidentNav } from "@/components/incidents/IncidentNav";
import { IncidentRegisterForm } from "@/components/incidents/IncidentRegisterForm";

export const metadata: Metadata = {
  title: "Register incident",
};

export default function IncidentRegisterPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Incidents</p>
          <h1>Register incident</h1>
          <p>
            Capture a new incident from a customer, clinic branch, or internal
            team. Branch is always required.
          </p>
          <IncidentNav current="/incidents/new" />
        </section>
        <IncidentRegisterForm />
      </div>
    </main>
  );
}
