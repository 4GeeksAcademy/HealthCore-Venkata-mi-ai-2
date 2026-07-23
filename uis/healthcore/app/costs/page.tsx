import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "Costs & Billing",
};

export default function CostsPage() {
  return (
    <section className="section">
      <div className="page-wrap">
        <h2>Costs & billing</h2>
        <p className="section-lead">
          HealthCore works with major US and UK payers. Tom Callahan&apos;s billing
          team tracks denial rates so claims stay clean and patients see clearer
          estimates before care.
        </p>
        <div className="card-grid">
          <article className="surface-card">
            <h3>Insurance & authorisations</h3>
            <p>
              Bring your insurance card to every visit. Our team helps with prior
              authorisations and resubmissions when payers request documentation.
            </p>
          </article>
          <article className="surface-card">
            <h3>Self-pay estimates</h3>
            <p>
              Ask your clinic for a self-pay estimate before elective visits.
              Average consultation fees vary by service type and location.
            </p>
          </article>
          <article className="surface-card">
            <h3>Price transparency</h3>
            <p>
              Request a plain-language estimate for common outpatient services.
              Contact billing support if a claim status looks unexpected.
            </p>
            <Link className="btn btn-primary" href="/care">
              Contact billing support
            </Link>
          </article>
        </div>
      </div>
    </section>
  );
}
