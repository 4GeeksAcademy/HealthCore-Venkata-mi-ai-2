/**
 * Single backoffice telemetry client. Call track() only.
 * Envelope fields are added here. Callers pass event_type and allowlisted properties.
 */

const SCHEMA_VERSION = "1.0.0";
const FLUSH_MS = 10_000;
const MAX_BATCH = 20;
const MAX_ATTEMPTS = 3;
const SESSION_KEY = "healthcore.telemetry.session";

const SECTION_PATHS = new Set([
  "/",
  "/ops",
  "/incidents",
  "/suppliers",
  "/inventory",
  "/inventory/inbound",
  "/inventory/outbound",
  "/inventory/orders",
  "/hiring",
  "/hiring/candidates/[id]",
  "/login",
  "/register",
  "/forgot-password",
  "/reset-password",
  "/account/profile",
  "/account/change-password",
]);

const ALLOW: Record<string, readonly string[]> = {
  inbound_order_created: ["order_id", "product_id", "sku", "quantity"],
  outbound_order_created: ["order_id", "product_id", "sku", "quantity", "threshold_crossed"],
  order_validation_failed: [
    "reason",
    "status_code",
    "route",
    "product_id",
    "sku",
    "quantity",
    "available_stock",
  ],
  direct_stock_edit_rejected: ["route", "rejected_fields"],
  stock_threshold_triggered: [
    "order_id",
    "product_id",
    "sku",
    "threshold",
    "previous_stock",
    "current_stock",
  ],
  product_created: ["product_id", "sku", "threshold", "below_threshold"],
  login_failed: ["reason"],
  login_succeeded: ["role"],
  session_expired: ["reason"],
  password_reset_failed: ["reason"],
  password_change_failed: ["reason"],
  section_viewed: ["path"],
  flow_started: ["flow"],
  flow_abandoned: ["flow"],
  api_latency_recorded: ["method", "route_template", "status_code", "duration_ms", "cache_status"],
  page_load_recorded: ["path", "duration_ms", "load_kind"],
  api_request_failed: ["method", "route_template", "status_code"],
  frontend_error_captured: ["error_name", "path"],
  incident_analysis_completed: ["total_processed", "total_valid", "total_invalid", "duration_ms"],
  supplier_record_changed: ["supplier_id", "action"],
  web_vital_recorded: ["name", "value", "path"],
};

type Envelope = {
  eventId: string;
  timestamp: string;
  sessionId: string;
  userId: string | null;
  event_type: string;
  schemaVersion: string;
  requestId: string;
  properties: Record<string, unknown>;
};

const queue: Envelope[] = [];
let flushTimer: number | null = null;
let lifecycleInstalled = false;
const seenSection = new Map<string, number>();
const seenPageLoad = new Map<string, number>();
const seenLatency = new Map<string, number>();
const seenVital = new Map<string, number>();
const openFlows = new Set<string>();

export function sectionPath(pathname: string): string | null {
  if (SECTION_PATHS.has(pathname)) return pathname;
  if (pathname.startsWith("/hiring/candidates/")) return "/hiring/candidates/[id]";
  return null;
}

export function allowlistedProperties(
  eventType: string,
  properties: Record<string, unknown>,
): Record<string, unknown> | null {
  const keys = ALLOW[eventType];
  if (!keys) return null;
  const next: Record<string, unknown> = {};
  for (const key of keys) {
    if (properties[key] !== undefined) next[key] = properties[key];
  }
  return next;
}

function shouldThrottle(eventType: string, properties: Record<string, unknown>): boolean {
  const now = Date.now();
  if (eventType === "section_viewed") {
    const path = String(properties.path ?? "");
    const previous = seenSection.get(path) ?? 0;
    if (now - previous < 30_000) return true;
    seenSection.set(path, now);
  }
  if (eventType === "page_load_recorded") {
    const path = String(properties.path ?? "");
    const previous = seenPageLoad.get(path) ?? 0;
    if (now - previous < 60_000) return true;
    seenPageLoad.set(path, now);
  }
  if (eventType === "api_latency_recorded") {
    const duration = Number(properties.duration_ms);
    if (!Number.isFinite(duration) || duration < 200) return true;
    const key = `${properties.method} ${properties.route_template}`;
    const previous = seenLatency.get(key) ?? 0;
    if (now - previous < 60_000) return true;
    seenLatency.set(key, now);
  }
  if (eventType === "web_vital_recorded") {
    const key = `${properties.name} ${properties.path}`;
    const previous = seenVital.get(key) ?? 0;
    if (now - previous < 60_000) return true;
    seenVital.set(key, now);
  }
  if (eventType === "flow_started") {
    const flow = String(properties.flow ?? "");
    if (openFlows.has(flow)) return true;
    openFlows.add(flow);
  }
  if (eventType === "flow_abandoned") {
    const flow = String(properties.flow ?? "");
    openFlows.delete(flow);
  }
  return false;
}

function sessionId(): string {
  const existing = window.sessionStorage.getItem(SESSION_KEY);
  if (existing) return existing;
  const created = window.crypto.randomUUID();
  window.sessionStorage.setItem(SESSION_KEY, created);
  return created;
}

function userIdFromToken(): string | null {
  const token = window.localStorage.getItem("healthcore.backoffice.access_token");
  if (!token) return null;
  const part = token.split(".")[1];
  if (!part) return null;
  try {
    const json = JSON.parse(
      window.atob(part.replace(/-/g, "+").replace(/_/g, "/")),
    ) as { sub?: unknown };
    return typeof json.sub === "string" && json.sub.length > 0 ? json.sub : null;
  } catch {
    return null;
  }
}

function endpoint(): string | null {
  const configured = process.env.NEXT_PUBLIC_TELEMETRY_ENDPOINT;
  return configured ? configured : null;
}

function scheduleFlush(): void {
  if (flushTimer !== null) return;
  flushTimer = window.setTimeout(() => {
    flushTimer = null;
    void flush("fetch");
  }, FLUSH_MS);
}

async function postBatch(events: Envelope[]): Promise<boolean> {
  const url = endpoint();
  if (!url) return false;
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ events }),
      keepalive: true,
    });
    return response.ok;
  } catch {
    return false;
  }
}

async function flush(mode: "fetch" | "beacon"): Promise<void> {
  if (queue.length === 0) return;
  const batch = queue.splice(0, queue.length);
  if (flushTimer !== null) {
    window.clearTimeout(flushTimer);
    flushTimer = null;
  }
  const url = endpoint();
  if (!url) return;
  if (mode === "beacon" && typeof navigator.sendBeacon === "function") {
    const blob = new Blob([JSON.stringify({ events: batch })], {
      type: "application/json",
    });
    if (navigator.sendBeacon(url, blob)) return;
  }
  let wait = 200;
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt += 1) {
    if (await postBatch(batch)) return;
    await new Promise((resolve) => {
      window.setTimeout(resolve, wait);
    });
    wait *= 2;
  }
}

export function installTelemetryLifecycle(): void {
  if (lifecycleInstalled || typeof window === "undefined") return;
  lifecycleInstalled = true;
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "hidden") {
      void flush("beacon");
    }
  });
}

export function track(eventType: string, properties: Record<string, unknown>): void {
  if (typeof window === "undefined") return;
  const allowed = allowlistedProperties(eventType, properties);
  if (!allowed || shouldThrottle(eventType, allowed)) return;
  installTelemetryLifecycle();
  queue.push({
    eventId: window.crypto.randomUUID(),
    timestamp: new Date().toISOString(),
    sessionId: sessionId(),
    userId: userIdFromToken(),
    event_type: eventType,
    schemaVersion: SCHEMA_VERSION,
    requestId: window.crypto.randomUUID(),
    properties: allowed,
  });
  if (queue.length >= MAX_BATCH) {
    void flush("fetch");
    return;
  }
  scheduleFlush();
}

export function routeTemplate(url: string): string {
  try {
    const path = new URL(url, "http://localhost").pathname;
    return path.replace(/\/\d+(?=\/|$)/g, "/{id}");
  } catch {
    return url;
  }
}
