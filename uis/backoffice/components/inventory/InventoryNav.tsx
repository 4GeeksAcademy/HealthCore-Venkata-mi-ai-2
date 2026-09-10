import Link from "next/link";

const LINKS = [
  { href: "/inventory", label: "Stock" },
  { href: "/inventory/inbound", label: "Inbound" },
  { href: "/inventory/outbound", label: "Outbound" },
  { href: "/inventory/orders", label: "Order history" },
] as const;

export function InventoryNav({ current }: { current: string }) {
  return (
    <nav className="inline-actions" aria-label="Inventory">
      {LINKS.map((link) => (
        <Link
          key={link.href}
          className={
            link.href === current ? "link-button" : "link-button secondary"
          }
          href={link.href}
        >
          {link.label}
        </Link>
      ))}
    </nav>
  );
}
