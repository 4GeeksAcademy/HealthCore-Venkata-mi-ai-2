import Link from "next/link";
import { siteBrand } from "@/lib/site-content";

const legalLinks = [
  { href: "/about", label: "Privacy Statement" },
  { href: "/about", label: "Notice of Privacy Practices" },
  { href: "/costs", label: "Price Transparency" },
  { href: "/about", label: "Terms of Use" },
] as const;

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <div className="page-wrap footer-grid">
        <div>
          <h2>Contact us</h2>
          <p>{siteBrand.address}</p>
          <p>
            <a href={siteBrand.phoneHref}>{siteBrand.phoneDisplay}</a>
          </p>
          <Link href="/care">Send us a message</Link>
        </div>
        <div>
          <h2>Our beliefs</h2>
          <p>
            HealthCore delivers advanced, simplified outpatient care with trusted
            clinicians, bilingual support, and compliance-first digital practices
            across HIPAA and UK GDPR environments.
          </p>
          <Link href="/about">Learn more</Link>
        </div>
        <div>
          <h2>Patients</h2>
          <p>
            <Link href="/care">Get care now</Link>
          </p>
          <p>
            <Link href="/locations">Find a clinic</Link>
          </p>
          <p>
            <Link href="/doctors">Find a doctor</Link>
          </p>
        </div>
      </div>
      <div className="page-wrap footer-legal">
        <span>&copy; {new Date().getFullYear()} HealthCore. All rights reserved.</span>
        <div style={{ display: "flex", flexWrap: "wrap", gap: "1rem" }}>
          {legalLinks.map((link) => (
            <Link key={link.label} href={link.href}>
              {link.label}
            </Link>
          ))}
        </div>
      </div>
    </footer>
  );
}
