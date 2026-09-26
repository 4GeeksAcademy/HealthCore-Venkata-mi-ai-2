import type { Metadata } from "next";
import { TelemetryRoot } from "@/components/telemetry/TelemetryRoot";
import "./globals.css";

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
    <html lang="en" className="h-full antialiased">
      <body className="app-body">
        <TelemetryRoot />
        {children}
      </body>
    </html>
  );
}
