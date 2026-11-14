import Link from "next/link";

const LINKS = [
  { href: "/incidents", label: "List & summary" },
  { href: "/incidents/new", label: "Register" },
  { href: "/incidents/analyze", label: "CSV analyzer" },
] as const;

export function IncidentNav({ current }: { current: string }) {
  return (
    <nav className="inline-actions" aria-label="Incidents">
      {LINKS.map((link) => (
        <Link
          key={link.href}
          className={
            current === link.href ? "link-button" : "link-button secondary"
          }
          href={link.href}
          prefetch={false}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
