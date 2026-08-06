import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
import { branding } from "@/lib/branding";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    default: "HealthCore Backoffice",
    template: "%s | HealthCore Backoffice",
  },
  description:
    "Internal HealthCore Digital workspace for hiring, operations, and clinic leadership tools.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="app-body">
        <div className="backoffice-topnav">
          <div className="backoffice-topnav-inner">
            <Link href="/" className="backoffice-brand">
              {branding.companyName} Backoffice
            </Link>
            <nav aria-label="Backoffice">
              <Link href="/">Home</Link>
              <Link href="/ops">Milestone 2 ops</Link>
              <Link href="/incidents">Incident analysis</Link>
              <Link href="/hiring">Hiring tracker</Link>
            </nav>
          </div>
        </div>
        {children}
      </body>
    </html>
  );
}
