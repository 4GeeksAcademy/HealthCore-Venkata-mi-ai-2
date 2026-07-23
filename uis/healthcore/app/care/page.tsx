import type { Metadata } from "next";
import Link from "next/link";
import { PatientSignupForm } from "@/components/PatientSignupForm";
import { siteBrand } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "Get Care Now",
};

export default function CarePage() {
  return (
    <section className="section">
      <div className="page-wrap">
        <h2>Get care now</h2>
        <p className="section-lead">
          Need same-day or urgent outpatient support? Call {siteBrand.phoneDisplay}
          or reserve a spot below. Walk-ins are welcome at most HealthCore clinics.
        </p>
        <div className="card-grid" style={{ marginBottom: "2rem" }}>
          <article className="surface-card">
            <h3>Call the network line</h3>
            <p>Speak with bilingual patient support for routing to the right clinic.</p>
            <a className="btn btn-primary" href={siteBrand.phoneHref}>
              Call {siteBrand.phoneDisplay}
            </a>
          </article>
          <article className="surface-card">
            <h3>Find a clinic</h3>
            <p>Choose a US or UK location and confirm hours before you travel.</p>
            <Link className="btn btn-primary" href="/locations">
              View locations
            </Link>
          </article>
        </div>
        <div style={{ maxWidth: "720px" }}>
          <PatientSignupForm />
        </div>
      </div>
    </section>
  );
}
