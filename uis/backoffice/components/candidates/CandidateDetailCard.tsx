import { CandidateRecord } from "@/types/candidate";

interface CandidateDetailCardProps {
  candidate: CandidateRecord;
}

export function CandidateDetailCard({ candidate }: CandidateDetailCardProps) {
  return (
    <section className="section-card">
      <header>
        <h2>{candidate.fullName}</h2>
        <p>
          {candidate.position} · {candidate.status} · {candidate.stage}
        </p>
      </header>

      <dl className="detail-list">
        <DetailItem label="Email" value={candidate.email} />
        <DetailItem label="Phone" value={candidate.phone} />
        <DetailItem label="Position applied for" value={candidate.position} />
        <DetailItem label="LinkedIn" value={candidate.linkedinUrl || "Not provided"} href={candidate.linkedinUrl} />
        <DetailItem label="CV link" value={candidate.cvUrl || "Not provided"} href={candidate.cvUrl} />
        <DetailItem label="Experience" value={candidate.experience || "Not provided"} />
        <DetailItem label="Status" value={candidate.status} />
        <DetailItem label="Stage" value={candidate.stage} />
        <DetailItem label="Application date" value={formatDate(candidate.applicationDate)} />
      </dl>
    </section>
  );
}

function DetailItem({
  label,
  value,
  href,
}: {
  label: string;
  value: string;
  href?: string;
}) {
  return (
    <div>
      <dt>{label}</dt>
      <dd>
        {href ? (
          <a href={href} target="_blank" rel="noreferrer">
            {value}
          </a>
        ) : (
          value
        )}
      </dd>
    </div>
  );
}

function formatDate(value: string) {
  const date = new Date(value);

  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString();
}