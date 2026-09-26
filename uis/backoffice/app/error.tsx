"use client";

import Link from "next/link";
import { useEffect } from "react";
import { sectionPath, track } from "@/lib/telemetry";

export default function BackofficeError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    const path = sectionPath(window.location.pathname) ?? "/";
    track("frontend_error_captured", {
      error_name: (error.name || "Error").slice(0, 64),
      path,
    });
  }, [error]);

  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="section-card">
          <h1>Something went wrong</h1>
          <p>The backoffice could not finish loading this page.</p>
          <div className="inline-actions">
            <button type="button" className="button" onClick={() => reset()}>
              Try again
            </button>
            <Link className="link-button secondary" href="/">
              Back to home
            </Link>
          </div>
        </section>
      </div>
    </main>
  );
}
