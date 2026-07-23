import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About HealthCore",
};

export default function AboutPage() {
  return (
    <section className="section">
      <div className="page-wrap">
        <h2>About HealthCore</h2>
        <p className="section-lead">
          Founded in 2011, HealthCore has grown into a cross-border outpatient
          healthcare network dedicated to accessible care, operational quality, and
          compliance-first data practices across HIPAA and UK GDPR environments.
        </p>
        <div className="card-grid">
          <article className="surface-card">
            <h3>Our network</h3>
            <p>
              Twelve clinics across Texas, Florida, Georgia, London, and Manchester
              serve roughly 600 patient visits each week with more than 200 staff.
            </p>
          </article>
          <article className="surface-card">
            <h3>HealthCore Digital</h3>
            <p>
              Led by CTO James Osei, HealthCore Digital modernises billing denial
              tracking, no-show cost estimation, CME compliance, and workforce
              hiring tools for clinic leaders.
            </p>
          </article>
          <article className="surface-card">
            <h3>Privacy commitment</h3>
            <p>
              We treat patient-adjacent data carefully. Public demos use synthetic
              identifiers only and never log real PHI.
            </p>
          </article>
        </div>
      </div>
    </section>
  );
}
