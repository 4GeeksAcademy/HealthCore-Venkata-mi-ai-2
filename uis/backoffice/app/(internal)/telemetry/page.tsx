"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ErrorActions } from "@/components/async/ErrorActions";

type MetricRow = Record<string, string | number | null>;

type ReportBody = {
  period?: { from?: string; to?: string };
  metrics?: Record<string, MetricRow[]>;
};

const METRIC_LABELS: { key: string; title: string }[] = [
  { key: "events_per_day", title: "Events per day" },
  { key: "error_rate_by_type", title: "Error rate by type" },
  { key: "latency_per_day", title: "API latency per day" },
  { key: "auth_failure_rate", title: "Login failure rate" },
];

export default function TelemetryReportPage() {
  const [report, setReport] = useState<ReportBody | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch("/hc-api/telemetry/report");
      if (!response.ok) {
        throw new Error("unavailable");
      }
      const body = (await response.json()) as ReportBody;
      setReport(body);
    } catch {
      setReport(null);
      setError("The telemetry report could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Engineering</p>
          <h1>Telemetry report</h1>
          <p>
            Operational health of the backoffice: event volume, errors, API latency, and login
            failures. This is not a purchasing or executive report.
          </p>
          <p>
            Period: {report?.period?.from ?? "…"} to {report?.period?.to ?? "…"}
          </p>
          <div className="inline-actions">
            <Link className="link-button secondary" href="/" prefetch={false}>
              Back to welcome
            </Link>
          </div>
        </section>

        {loading ? (
          <section className="section-card">
            <p className="muted-text" role="status">
              Loading telemetry report…
            </p>
          </section>
        ) : null}

        {error ? (
          <section className="section-card" role="alert">
            <p>{error}</p>
            <ErrorActions onRetry={() => void load()} />
          </section>
        ) : null}

        {!loading && !error
          ? METRIC_LABELS.map((metric) => {
              const rows = report?.metrics?.[metric.key] ?? [];
              const columns = rows[0] ? Object.keys(rows[0]) : [];
              return (
                <section className="section-card" key={metric.key}>
                  <h2>{metric.title}</h2>
                  {rows.length === 0 ? (
                    <p className="muted-text">No events in this period.</p>
                  ) : (
                    <table>
                      <thead>
                        <tr>
                          {columns.map((column) => (
                            <th key={column}>{column}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {rows.map((row, index) => (
                          <tr key={`${metric.key}-${index}`}>
                            {columns.map((column) => (
                              <td key={column}>{String(row[column] ?? "")}</td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </section>
              );
            })
          : null}
      </div>
    </main>
  );
}
