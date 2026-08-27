"use client";

import { useCallback, useRef, useState } from "react";
import { authedFetch } from "@/lib/authed-fetch";

export type IncidentAnalysisSummary = {
  total_processed: number;
  total_valid: number;
  total_invalid: number;
  invalid_by_type: Record<string, number>;
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  avg_satisfaction_closed: number | null;
  closed_with_score_count: number;
};

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_INCIDENTS_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8001"
  );
}

function BreakdownList({
  title,
  data,
}: {
  title: string;
  data: Record<string, number>;
}) {
  const entries = Object.entries(data);
  return (
    <section className="section-card">
      <h2>{title}</h2>
      {entries.length === 0 ? (
        <p>None</p>
      ) : (
        <ul>
          {entries.map(([key, value]) => (
            <li key={key}>
              <strong>{key}</strong>: {value}
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}

export function IncidentAnalyzerPanel() {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);
  const [busy, setBusy] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<IncidentAnalysisSummary | null>(null);

  const runAnalyze = useCallback(async (file: File) => {
    setBusy(true);
    setError(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const res = await authedFetch(`${apiBase()}/api/incidents/analyze`, {
        method: "POST",
        body,
      });
      const payload = await res.json().catch(() => null);
      setSummary(payload as IncidentAnalysisSummary);
    } catch (err) {
      setSummary(null);
      const message =
        err instanceof Error ? err.message : "Upload failed.";
      const hint =
        message === "Failed to fetch"
          ? ` Cannot reach the Incident API at ${apiBase()}. Start it with: cd services/api && python -m uvicorn app.main:app --reload --port 8001`
          : "";
      setError(`${message}.${hint}`);
    } finally {
      setBusy(false);
    }
  }, []);

  const onExport = useCallback(async () => {
    setExporting(true);
    setError(null);
    try {
      const res = await authedFetch(`${apiBase()}/api/incidents/results/export`);
      const blob = await res.blob();
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "results.csv";
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Export failed.");
    } finally {
      setExporting(false);
    }
  }, []);

  const onFileChosen = (file: File | undefined) => {
    if (!file) return;
    void runAnalyze(file);
  };

  return (
    <div style={{ display: "grid", gap: "1.5rem" }}>
      <section className="section-card">
        <h2>Upload incident CSV</h2>
        <p>
          Drag and drop a CSV matching the Incident File Analyzer CONTEXT, or
          choose a file. Analysis runs on the FastAPI service at{" "}
          <code>{apiBase()}</code>.
        </p>
        <div
          className="incident-dropzone"
          data-dragging={dragging ? "true" : "false"}
          onDragEnter={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragOver={(e) => {
            e.preventDefault();
            setDragging(true);
          }}
          onDragLeave={(e) => {
            e.preventDefault();
            setDragging(false);
          }}
          onDrop={(e) => {
            e.preventDefault();
            setDragging(false);
            onFileChosen(e.dataTransfer.files?.[0]);
          }}
          onClick={() => inputRef.current?.click()}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => {
            if (e.key === "Enter" || e.key === " ") {
              e.preventDefault();
              inputRef.current?.click();
            }
          }}
        >
          <p>
            {busy
              ? "Analyzing…"
              : "Drop CSV here, or click to select a file"}
          </p>
          <input
            ref={inputRef}
            type="file"
            accept=".csv,text/csv"
            hidden
            onChange={(e) => onFileChosen(e.target.files?.[0])}
          />
        </div>
        {error ? <p className="feedback error">{error}</p> : null}
      </section>

      {summary ? (
        <>
          <section className="section-card">
            <header
              style={{
                display: "flex",
                justifyContent: "space-between",
                gap: "1rem",
                flexWrap: "wrap",
                alignItems: "center",
              }}
            >
              <h2>General metrics</h2>
              <button
                type="button"
                className="link-button"
                onClick={() => void onExport()}
                disabled={exporting}
              >
                {exporting ? "Downloading..." : "Download results CSV"}
              </button>
            </header>
            <ul>
              <li>
                <strong>Total processed</strong>: {summary.total_processed}
              </li>
              <li>
                <strong>Valid</strong>: {summary.total_valid}
              </li>
              <li>
                <strong>Invalid</strong>: {summary.total_invalid}
              </li>
              <li>
                <strong>Avg satisfaction (closed with score)</strong>:{" "}
                {summary.avg_satisfaction_closed ?? "n/a"}
              </li>
              <li>
                <strong>Closed cases with score</strong>:{" "}
                {summary.closed_with_score_count}
              </li>
            </ul>
          </section>

          {summary.total_invalid > 0 ? (
            <BreakdownList
              title="Invalid records by problem type"
              data={summary.invalid_by_type}
            />
          ) : (
            <section className="section-card">
              <h2>Invalid records</h2>
              <p>No invalid records in this file.</p>
            </section>
          )}

          <BreakdownList
            title="Breakdown by category"
            data={summary.by_category}
          />
          <BreakdownList title="Breakdown by status" data={summary.by_status} />
        </>
      ) : null}
    </div>
  );
}
