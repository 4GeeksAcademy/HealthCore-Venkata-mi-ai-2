import Link from "next/link";
import { branding } from "@/lib/branding";
import { CandidateRecord } from "@/types/candidate";

interface CandidateTableProps {
  records: CandidateRecord[];
}

export function CandidateTable({ records }: CandidateTableProps) {
  if (!records.length) {
    return (
      <div className="empty-state">
        No {branding.candidatePlural.toLowerCase()} match the current filters.
      </div>
    );
  }

  return (
    <div className="table-shell">
      <table className="data-table">
      <thead>
        <tr>
          <th>Full name</th>
          <th>{branding.positionLabel}</th>
          <th>{branding.statusLabel}</th>
          <th>{branding.stageLabel}</th>
          <th>Open</th>
        </tr>
      </thead>
      <tbody>
        {records.map((record) => (
          <tr key={record.id}>
            <td data-label="Full name">
              <strong>{record.fullName}</strong>
              <div className="muted-text">{record.email}</div>
            </td>
            <td data-label={branding.positionLabel}>{record.position}</td>
            <td data-label={branding.statusLabel}>
              <span className="pill">{record.status}</span>
            </td>
            <td data-label={branding.stageLabel}>{record.stage}</td>
            <td data-label="Open" className="table-action-cell">
              <Link className="link-button secondary" href={`/candidates/${record.id}`}>
                View details
              </Link>
            </td>
          </tr>
        ))}
      </tbody>
      </table>
    </div>
  );
}