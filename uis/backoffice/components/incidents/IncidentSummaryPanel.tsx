"use client";

import { useCallback, useEffect, useState } from "react";
import { fetchIncidentSummary, type IncidentSummary } from "@/lib/incidents-api";
import { branchLabel, statusLabel } from "@/lib/incidents-constants";
import { getUserFacingError } from "@/lib/user-facing-error";
import Link from "next/link";

function MetricBlock({
  title,
  data,
  labelFor,
}: {
  title: string;
  data: Record<string, number>;
  labelFor?: (key: string) => string;
}) {
  const entries = Object.entries(data).filter(([, value]) => value > 0);
  return (
    <section className="section-card">
      <h3>{title}</h3>
      {entries.length === 0 ? (
        <p className="muted-text">No incidents in this group yet.</p>
      ) : (
        <ul>
          {entries.map(([key, value]) => (
            <li key={key}>
              <strong>{labelFor ? labelFor(key) : key}</strong>: {value}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function IncidentSummaryPanel() {
  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchIncidentSummary();
      setSummary(data);
    } catch (err) {
      setSummary(null);
      setError(
        getUserFacingError(
          err,
          "Could not load incident summary. Please try again.",
        ),
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) {
    return (
      <section className="section-card" aria-busy="true">
        <p role="status">Loading summary…</p>
      </section>
    );
  }

  if (error) {
    return (
      <section className="section-card">
        <p role="alert">{error}</p>
        <div className="inline-actions">
          <button type="button" className="link-button" onClick={() => void load()}>
            Retry summary
          </button>
          <Link className="link-button secondary" href="/">
            Home
          </Link>
        </div>
      </section>
    );
  }

  if (!summary) {
    return null;
  }

  return (
    <div>
      <p className="muted-text">Total incidents: {summary.total}</p>
      <div
        style={{
          display: "grid",
          gap: "1rem",
          gridTemplateColumns: "repeat(auto-fit, minmax(14rem, 1fr))",
        }}
      >
        <MetricBlock title="By status" data={summary.by_status} labelFor={statusLabel} />
        <MetricBlock title="By category" data={summary.by_category} />
        <MetricBlock title="By origin" data={summary.by_origin} />
        <MetricBlock title="By branch" data={summary.by_branch} labelFor={branchLabel} />
      </div>
    </div>
  );
}
