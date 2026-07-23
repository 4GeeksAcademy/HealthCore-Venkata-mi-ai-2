import Link from "next/link";
import { ServiceCard } from "@/components/ServiceCard";
import { PatientSignupForm } from "@/components/PatientSignupForm";
import { services, siteBrand } from "@/lib/site-content";

export default function HomePage() {
  const featured = services.slice(0, 3);

  return (
    <>
      <section className="hero">
        <div className="page-wrap">
          <p className="eyebrow">Healthcare reimagined</p>
          <h1>Advanced, simplified healthcare for every stage of life.</h1>
          <p>
            HealthCore combines trusted clinical teams with modern digital
            coordination so patients can access care faster across 12 clinics in
            the United States and United Kingdom.
          </p>
          <div style={{ display: "flex", gap: "0.75rem", flexWrap: "wrap" }}>
            <Link className="btn btn-secondary" href="/care">
              Get care now
            </Link>
            <Link className="btn btn-secondary" href="/locations">
              Find a location
            </Link>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="page-wrap">
          <h2>Care designed for outpatient excellence</h2>
          <p className="section-lead">
            Primary care, urgent visits, and specialty support — built for the
            same operational reliability HealthCore Digital reports to clinic
            leaders every Monday.
          </p>
          <div className="card-grid">
            {featured.map((service) => (
              <ServiceCard key={service.id} service={service} />
            ))}
          </div>
        </div>
      </section>

      <section className="section" style={{ background: "#fff" }}>
        <div className="page-wrap">
          <h2>Built for trust</h2>
          <ul className="meta-list">
            <li>12 clinics across Texas, Florida, Georgia, London, and Manchester</li>
            <li>~600 patient visits coordinated each week</li>
            <li>200+ clinical and administrative staff</li>
            <li>Call {siteBrand.phoneDisplay} for bilingual patient support</li>
          </ul>
        </div>
      </section>

      <section className="section">
        <div className="page-wrap" style={{ maxWidth: "720px" }}>
          <PatientSignupForm />
        </div>
      </section>
    </>
  );
}
