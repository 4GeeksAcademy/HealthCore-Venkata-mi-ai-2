import type { Supplier, SupplierCreate, SupplierStatus } from "@/types/supplier";
import { authedFetch } from "@/lib/authed-fetch";
import { track } from "@/lib/telemetry";
import { readResponseJson } from "@/lib/user-facing-error";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_SUPPLIERS_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8001"
  );
}

export async function fetchSuppliers(params?: {
  country?: string;
  category?: string;
}): Promise<Supplier[]> {
  const qs = new URLSearchParams();
  if (params?.country) qs.set("country", params.country);
  if (params?.category) qs.set("category", params.category);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const res = await authedFetch(`${apiBase()}/suppliers${suffix}`, {
    cache: "no-store",
  });
  return readResponseJson<Supplier[]>(res);
}

export async function createSupplier(payload: SupplierCreate): Promise<Supplier> {
  const res = await authedFetch(`${apiBase()}/suppliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const created = await readResponseJson<Supplier>(res);
  track("supplier_record_changed", { supplier_id: created.id, action: "created" });
  return created;
}

export async function updateSupplierRate(
  id: number,
  monthly_rate: number,
): Promise<Supplier> {
  const res = await authedFetch(`${apiBase()}/suppliers/${id}/rate`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ monthly_rate }),
  });
  const updated = await readResponseJson<Supplier>(res);
  track("supplier_record_changed", { supplier_id: id, action: "rate_updated" });
  return updated;
}

export async function updateSupplierStatus(
  id: number,
  status: SupplierStatus,
): Promise<Supplier> {
  const res = await authedFetch(`${apiBase()}/suppliers/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  const updated = await readResponseJson<Supplier>(res);
  track("supplier_record_changed", { supplier_id: id, action: "status_updated" });
  return updated;
}
