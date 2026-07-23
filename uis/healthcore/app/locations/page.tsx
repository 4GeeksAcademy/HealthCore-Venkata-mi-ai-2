import type { Metadata } from "next";
import { clinics } from "@/lib/site-content";

export const metadata: Metadata = {
  title: "Locations",
};

export default function LocationsPage() {
  return (
    <section className="section">
      <div className="page-wrap">
        <h2>Clinic locations</h2>
        <p className="section-lead">
          HealthCore operates outpatient clinics across the United States and
          United Kingdom. Visit or call the site closest to you.
        </p>
        <div className="card-grid">
          {clinics.map((clinic) => (
            <article key={clinic.locationId} className="surface-card">
              <h3>{clinic.name}</h3>
              <p>{clinic.addressLine}</p>
              <ul className="meta-list">
                <li>
                  {clinic.city}, {clinic.stateOrCountry} ({clinic.country})
                </li>
                <li>
                  <a href={`tel:${clinic.phone.replace(/[^\d+]/g, "")}`}>
                    {clinic.phone}
                  </a>
                </li>
                <li>Clinic ID: {clinic.locationId}</li>
              </ul>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
