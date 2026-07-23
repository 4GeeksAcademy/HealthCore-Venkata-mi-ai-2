import Image from "next/image";
import Link from "next/link";
import { primaryNav, siteBrand } from "@/lib/site-content";

export function SiteHeader() {
  return (
    <header className="site-header">
      <div className="page-wrap header-inner">
        <Link href="/" className="brand" aria-label="HealthCore home">
          <Image
            src="/healthcore-logo.svg"
            alt=""
            width={36}
            height={36}
            priority
          />
          <span>{siteBrand.name}</span>
        </Link>
        <nav className="nav" aria-label="Primary">
          {primaryNav.map((item) => (
            <Link key={item.href} href={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
        <a className="header-phone" href={siteBrand.phoneHref}>
          {siteBrand.phoneDisplay}
        </a>
      </div>
    </header>
  );
}
