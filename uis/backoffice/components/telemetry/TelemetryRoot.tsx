"use client";

import { usePathname } from "next/navigation";
import { useReportWebVitals } from "next/web-vitals";
import { useEffect } from "react";
import { installTelemetryLifecycle, sectionPath, track } from "@/lib/telemetry";

const VITAL_NAMES = new Set(["LCP", "INP", "CLS", "FCP", "TTFB"]);

export function TelemetryRoot() {
  const pathname = usePathname();

  useReportWebVitals((metric) => {
    const path = sectionPath(window.location.pathname);
    if (!path || !VITAL_NAMES.has(metric.name)) return;
    track("web_vital_recorded", {
      name: metric.name,
      value: metric.value,
      path,
    });
  });

  useEffect(() => {
    installTelemetryLifecycle();
    const path = sectionPath(pathname);
    if (!path) return;

    track("section_viewed", { path });
    const started = performance.now();
    const frame = window.requestAnimationFrame(() => {
      if (!document.querySelector("h1")) return;
      const nav = performance.getEntriesByType("navigation")[0] as
        | PerformanceNavigationTiming
        | undefined;
      const durationMs =
        nav && started < 2000 ? nav.domContentLoadedEventEnd : performance.now() - started;
      track("page_load_recorded", {
        path,
        duration_ms: durationMs,
        load_kind: nav?.type === "reload" ? "reload" : "navigate",
      });
    });

    const onError = (event: ErrorEvent) => {
      const name = event.error instanceof Error ? event.error.name : "Error";
      track("frontend_error_captured", { error_name: name.slice(0, 64), path });
    };
    const onReject = (event: PromiseRejectionEvent) => {
      const name = event.reason instanceof Error ? event.reason.name : "UnhandledRejection";
      track("frontend_error_captured", { error_name: name.slice(0, 64), path });
    };
    window.addEventListener("error", onError);
    window.addEventListener("unhandledrejection", onReject);
    return () => {
      window.cancelAnimationFrame(frame);
      window.removeEventListener("error", onError);
      window.removeEventListener("unhandledrejection", onReject);
    };
  }, [pathname]);

  return null;
}
