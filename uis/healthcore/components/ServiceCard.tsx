import Link from "next/link";
import type { ServiceOffering } from "@/types/content";

interface ServiceCardProps {
  service: ServiceOffering;
}

export function ServiceCard({ service }: ServiceCardProps) {
  return (
    <article className="surface-card">
      <h3>{service.title}</h3>
      <p>{service.description}</p>
      <Link className="btn btn-primary" href={service.href}>
        {service.ctaLabel}
      </Link>
    </article>
  );
}
