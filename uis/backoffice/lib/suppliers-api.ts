import type { Supplier, SupplierCreate, SupplierStatus } from "@/types/supplier";
import { authedFetch } from "@/lib/authed-fetch";

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
  return (await res.json()) as Supplier[];
}

export async function createSupplier(payload: SupplierCreate): Promise<Supplier> {
  const res = await authedFetch(`${apiBase()}/suppliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return (await res.json()) as Supplier;
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
  return (await res.json()) as Supplier;
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
  return (await res.json()) as Supplier;
}
