import type { Metadata } from "next";
import { clinicians } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "Doctors",
};

export default function DoctorsPage() {
  return (
    <section className="section">
      <div className="page-wrap">
        <h2>Our doctors and clinicians</h2>
        <p className="section-lead">
          Meet sample HealthCore clinicians across the outpatient network. Profiles
          use synthetic IDs for demonstration only.
        </p>
        <div className="card-grid">
          {clinicians.map((clinician) => (
            <article key={clinician.clinicianId} className="surface-card">
              <h3>{clinician.fullName}</h3>
              <p>
                {clinician.role} · {clinician.locationName}
              </p>
              <ul className="meta-list">
                {clinician.specialties.map((specialty) => (
                  <li key={specialty}>{specialty}</li>
                ))}
                <li>
                  {clinician.acceptingPatients
                    ? "Accepting new patients"
                    : "Waitlist only"}
                </li>
                <li>ID: {clinician.clinicianId}</li>
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
