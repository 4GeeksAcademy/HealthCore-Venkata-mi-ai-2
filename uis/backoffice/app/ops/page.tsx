import type { Metadata } from "next";
import Link from "next/link";
import { Milestone2OpsPanel } from "@/components/ops/Milestone2OpsPanel";

export const metadata: Metadata = {
  title: "Monday ops (Milestone 2)",
};

export default function OpsPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Operations</p>
          <h1>Milestone 2 ops dashboard</h1>
          <p>
            This screen integrates the Milestone 2 TypeScript utilities from{" "}
            <code>src/utils</code> and renders their results for Monday morning
            review.
          </p>
          <div className="inline-actions">
            <Link className="link-button secondary" href="/">
              Back to welcome
            </Link>
          </div>
        </section>

        <Milestone2OpsPanel />
      </div>
    </main>
  );
}
