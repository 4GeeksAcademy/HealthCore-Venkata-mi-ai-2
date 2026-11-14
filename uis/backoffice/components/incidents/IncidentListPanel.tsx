"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  fetchIncidents,
  patchIncidentStatus,
  type IncidentRecord,
} from "@/lib/incidents-api";
import {
  INCIDENT_BRANCHES,
  INCIDENT_ORIGINS,
  INCIDENT_STATUSES,
  NEXT_STATUSES,
  branchLabel,
  statusLabel,
  type IncidentStatus,
} from "@/lib/incidents-constants";
import { getUserFacingError } from "@/lib/user-facing-error";

export function IncidentListPanel() {
  const [status, setStatus] = useState("");
  const [origin, setOrigin] = useState("");
  const [branch, setBranch] = useState("");
  const [items, setItems] = useState<IncidentRecord[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [rowError, setRowError] = useState<string | null>(null);
  const [pendingId, setPendingId] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchIncidents({
        status: status || undefined,
        origin: origin || undefined,
        branch: branch || undefined,
      });
      setItems(data.items);
      setTotal(data.total);
    } catch (err) {
      setItems([]);
      setTotal(0);
      setError(
        getUserFacingError(
          err,
          "Could not load incidents. Please try again.",
        ),
      );
    } finally {
      setLoading(false);
    }
  }, [status, origin, branch]);

  useEffect(() => {
    void load();
  }, [load]);

  async function onStatusChange(incident: IncidentRecord, next: IncidentStatus) {
    if (next === incident.status) return;
    const previous = incident.status;
    setRowError(null);
    setPendingId(incident.id);
    setItems((current) =>
      current.map((row) =>
        row.id === incident.id ? { ...row, status: next } : row,
      ),
    );
    try {
      const updated = await patchIncidentStatus(incident.id, next);
      setItems((current) =>
        current.map((row) => (row.id === incident.id ? updated : row)),
      );
    } catch (err) {
      setItems((current) =>
        current.map((row) =>
          row.id === incident.id ? { ...row, status: previous } : row,
        ),
      );
      setRowError(
        getUserFacingError(
          err,
          "Could not update status. The previous value was restored.",
        ),
      );
    } finally {
      setPendingId(null);
    }
  }

  return (
    <section className="section-card">
      <h2>Incident list</h2>
      <div className="inline-actions" style={{ flexWrap: "wrap", gap: "0.75rem" }}>
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            <option value="">All</option>
            {INCIDENT_STATUSES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Origin
          <select value={origin} onChange={(e) => setOrigin(e.target.value)}>
            <option value="">All</option>
            {INCIDENT_ORIGINS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
        <label>
          Branch
          <select value={branch} onChange={(e) => setBranch(e.target.value)}>
            <option value="">All</option>
            {INCIDENT_BRANCHES.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </label>
      </div>

      {rowError ? (
        <p role="alert" className="notice-error">
          {rowError}
        </p>
      ) : null}

      {loading ? (
        <p role="status">Loading incidents…</p>
      ) : error ? (
        <div>
          <p role="alert">{error}</p>
          <div className="inline-actions">
            <button type="button" className="link-button" onClick={() => void load()}>
              Retry
            </button>
            <Link className="link-button secondary" href="/">
              Home
            </Link>
          </div>
        </div>
      ) : items.length === 0 ? (
        <p role="status">
          No incidents match these filters
          {total === 0 ? " (or none have been registered yet)" : ""}.
        </p>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table>
            <thead>
              <tr>
                <th>Title</th>
                <th>Category</th>
                <th>Origin</th>
                <th>Branch</th>
                <th>Status</th>
                <th>Updated</th>
              </tr>
            </thead>
            <tbody>
              {items.map((incident) => {
                const next = NEXT_STATUSES[incident.status] ?? [];
                return (
                  <tr key={incident.id}>
                    <td>
                      <strong>{incident.title}</strong>
                      <div className="muted-text" style={{ maxWidth: "18rem" }}>
                        {incident.description.slice(0, 120)}
                        {incident.description.length > 120 ? "…" : ""}
                      </div>
                    </td>
                    <td>{incident.category}</td>
                    <td>{incident.origin}</td>
                    <td>{branchLabel(incident.branch)}</td>
                    <td>
                      {next.length === 0 ? (
                        statusLabel(incident.status)
                      ) : (
                        <select
                          aria-label={`Update status for ${incident.title}`}
                          value={incident.status}
                          disabled={pendingId === incident.id}
                          onChange={(e) =>
                            void onStatusChange(
                              incident,
                              e.target.value as IncidentStatus,
                            )
                          }
                        >
                          <option value={incident.status}>
                            {statusLabel(incident.status)}
                          </option>
                          {next.map((value) => (
                            <option key={value} value={value}>
                              {statusLabel(value)}
                            </option>
                          ))}
                        </select>
                      )}
                    </td>
                    <td>{incident.updated_at}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
          <p className="muted-text">{total} incident(s)</p>
        </div>
      )}
    </section>
  );
}
