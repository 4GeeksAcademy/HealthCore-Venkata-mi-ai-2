import type { Supplier, SupplierCreate, SupplierStatus } from "@/types/supplier";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_SUPPLIERS_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8001"
  );
}

async function readError(res: Response): Promise<string> {
  try {
    const body = (await res.json()) as {
      detail?: string | Array<{ msg?: string }>;
    };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail)) {
      return body.detail
        .map((item) => item.msg)
        .filter(Boolean)
        .join("; ");
    }
  } catch {
    /* ignore */
  }
  return `Request failed (${res.status})`;
}

export async function fetchSuppliers(params?: {
  country?: string;
  category?: string;
}): Promise<Supplier[]> {
  const qs = new URLSearchParams();
  if (params?.country) qs.set("country", params.country);
  if (params?.category) qs.set("category", params.category);
  const suffix = qs.toString() ? `?${qs.toString()}` : "";
  const res = await fetch(`${apiBase()}/suppliers${suffix}`, {
    cache: "no-store",
  });
  if (!res.ok) throw new Error(await readError(res));
  return (await res.json()) as Supplier[];
}

export async function createSupplier(payload: SupplierCreate): Promise<Supplier> {
  const res = await fetch(`${apiBase()}/suppliers`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(await readError(res));
  return (await res.json()) as Supplier;
}

export async function updateSupplierRate(
  id: number,
  contract_rate: number,
): Promise<Supplier> {
  const res = await fetch(`${apiBase()}/suppliers/${id}/rate`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ contract_rate }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return (await res.json()) as Supplier;
}

export async function updateSupplierStatus(
  id: number,
  status: SupplierStatus,
): Promise<Supplier> {
  const res = await fetch(`${apiBase()}/suppliers/${id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ status }),
  });
  if (!res.ok) throw new Error(await readError(res));
  return (await res.json()) as Supplier;
}
