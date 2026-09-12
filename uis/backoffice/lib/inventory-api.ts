import { authedFetch } from "@/lib/authed-fetch";
import { readResponseJson } from "@/lib/user-facing-error";
import type {
  InventoryOrder,
  InventoryOrderCreate,
  InventoryProduct,
} from "@/types/inventory";

function apiBase(): string {
  return (
    process.env.NEXT_PUBLIC_INVENTORY_API_URL?.replace(/\/$/, "") ||
    "http://localhost:8001"
  );
}

function asFiniteNumber(value: unknown, fallback = 0): number {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

/** Map ORM dual-db JSON onto the MS5 backoffice display model. */
export function asProduct(row: Record<string, unknown>): InventoryProduct {
  const current = asFiniteNumber(
    row.current_stock,
    asFiniteNumber(row.stock, 0),
  );
  return {
    id: asFiniteNumber(row.id),
    name: String(row.name ?? ""),
    sku: String(row.sku ?? ""),
    stock: current,
    threshold: asFiniteNumber(row.threshold, 0),
  };
}

export function asOrder(row: Record<string, unknown>): InventoryOrder {
  const type = row.type === "outbound" ? "outbound" : "inbound";
  return {
    id: asFiniteNumber(row.id),
    product_id: asFiniteNumber(row.product_id),
    product_name: String(row.product_name ?? ""),
    quantity: asFiniteNumber(row.quantity, 0),
    type,
    notes: String(row.notes ?? ""),
    created_at: String(row.created_at ?? ""),
    created_by: String(row.created_by ?? row.user_uuid ?? ""),
  };
}

export async function fetchInventoryProducts(): Promise<InventoryProduct[]> {
  const res = await authedFetch(`${apiBase()}/inventory/products`, {
    cache: "no-store",
  });
  const rows = await readResponseJson<Record<string, unknown>[]>(res);
  return rows.map(asProduct);
}

export async function createInboundOrder(
  payload: InventoryOrderCreate,
): Promise<InventoryOrder> {
  const res = await authedFetch(`${apiBase()}/inventory/orders/inbound`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const row = await readResponseJson<Record<string, unknown>>(res);
  return asOrder({ ...row, type: "inbound" });
}

export async function createOutboundOrder(
  payload: InventoryOrderCreate,
): Promise<InventoryOrder> {
  const res = await authedFetch(`${apiBase()}/inventory/orders/outbound`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const row = await readResponseJson<Record<string, unknown>>(res);
  return asOrder({ ...row, type: "outbound" });
}

export async function fetchInventoryOrders(): Promise<InventoryOrder[]> {
  const res = await authedFetch(`${apiBase()}/inventory/orders`, {
    cache: "no-store",
  });
  const rows = await readResponseJson<Record<string, unknown>[]>(res);
  return rows.map(asOrder);
}
