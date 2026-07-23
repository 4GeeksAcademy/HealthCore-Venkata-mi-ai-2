import type { Metadata } from "next";
import { ServiceCard } from "@/components/ServiceCard";
import { services } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "Services & Specialties",
};

export default function ServicesPage() {
  return (
    <section className="section">
      <div className="page-wrap">
        <h2>Services & specialties</h2>
        <p className="section-lead">
          From primary care to chronic disease, preventive programs, and mental
          health — HealthCore delivers outpatient care with consistent clinical
          standards across every clinic.
        </p>
        <div className="card-grid">
          {services.map((service) => (
            <ServiceCard key={service.id} service={service} />
          ))}
        </div>
      </div>
    </section>
  );
}
