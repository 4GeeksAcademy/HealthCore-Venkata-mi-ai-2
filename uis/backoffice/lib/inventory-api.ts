import { authedFetch } from "@/lib/authed-fetch";
import {
  DEFAULT_CLINIC_ID,
  DEFAULT_COUNTRY,
  daysToExpiry,
  shouldFlagExpiry,
} from "@/lib/clinic-context";
import { trackInventoryFailure } from "@/lib/inventory-telemetry";
import { track } from "@/lib/telemetry";
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
    category: row.category != null ? String(row.category) : "consumable",
    expiry_date: row.expiry_date != null ? String(row.expiry_date) : null,
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
    clinic_id: String(row.clinic_id ?? DEFAULT_CLINIC_ID),
    country: String(row.country ?? DEFAULT_COUNTRY),
    department: row.department != null ? String(row.department) : null,
    sku: row.sku != null ? String(row.sku) : undefined,
    product_category:
      row.product_category != null ? String(row.product_category) : undefined,
    expiry_date: row.expiry_date != null ? String(row.expiry_date) : null,
    total_cost:
      row.total_cost === null || row.total_cost === undefined
        ? null
        : asFiniteNumber(row.total_cost),
  };
}

function maybeTrackExpiry(args: {
  product_id: number;
  sku: string;
  clinic_id: string;
  country: string;
  product_category: string;
  quantity: number;
  expiry_date?: string | null;
}): void {
  if (!shouldFlagExpiry(args.expiry_date)) return;
  track("supply_expiry_flagged", {
    product_id: args.product_id,
    sku: args.sku,
    clinic_id: args.clinic_id,
    country: args.country,
    product_category: args.product_category,
    quantity: args.quantity,
    expiry_date: args.expiry_date,
    days_to_expiry: daysToExpiry(args.expiry_date),
  });
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

export type OutboundWriteResult = InventoryOrder & {
  sku: string;
  threshold: number;
  previous_stock: number;
  current_stock: number;
  threshold_crossed: boolean;
  product_category?: string;
  expiry_date?: string | null;
};

export async function createOutboundOrder(
  payload: InventoryOrderCreate,
): Promise<OutboundWriteResult> {
  const res = await authedFetch(`${apiBase()}/inventory/orders/outbound`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const row = await readResponseJson<Record<string, unknown>>(res);
  const order = asOrder({ ...row, type: "outbound" });
  return {
    ...order,
    sku: String(row.sku ?? ""),
    threshold: asFiniteNumber(row.threshold, 0),
    previous_stock: asFiniteNumber(row.previous_stock, 0),
    current_stock: asFiniteNumber(row.current_stock, 0),
    threshold_crossed: row.threshold_crossed === true,
  };
}

export async function createMedicalSupply(payload: {
  name: string;
  sku: string;
  threshold: number;
  category?: string;
  expiry_date?: string | null;
  stock?: number;
  current_stock?: number;
}): Promise<InventoryProduct> {
  const body: Record<string, unknown> = {
    name: payload.name,
    sku: payload.sku,
    threshold: payload.threshold,
  };
  if (payload.category) body.category = payload.category;
  if (payload.expiry_date) body.expiry_date = payload.expiry_date;
  const rejected: Array<"stock" | "current_stock"> = [];
  if (payload.stock !== undefined) {
    body.stock = payload.stock;
    rejected.push("stock");
  }
  if (payload.current_stock !== undefined) {
    body.current_stock = payload.current_stock;
    rejected.push("current_stock");
  }
  try {
    const res = await authedFetch(`${apiBase()}/inventory/products`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const product = asProduct(await readResponseJson<Record<string, unknown>>(res));
    track("product_created", {
      product_id: product.id,
      sku: product.sku,
      threshold: product.threshold,
      below_threshold: product.stock < product.threshold,
      product_category: product.category ?? "consumable",
      expiry_date: product.expiry_date ?? undefined,
    });
    maybeTrackExpiry({
      product_id: product.id,
      sku: product.sku,
      clinic_id: DEFAULT_CLINIC_ID,
      country: DEFAULT_COUNTRY,
      product_category: String(product.category ?? "consumable"),
      quantity: product.stock,
      expiry_date: product.expiry_date,
    });
    return product;
  } catch (err) {
    if (
      rejected.length > 0 &&
      err instanceof Error &&
      err.message === "Stock cannot be modified directly. Register an inbound or outbound order."
    ) {
      track("direct_stock_edit_rejected", {
        route: "POST /inventory/products",
        rejected_fields: rejected,
      });
    } else {
      trackInventoryFailure("POST /inventory/products", err, { sku: payload.sku });
    }
    throw err;
  }
}

export async function fetchInventoryOrders(): Promise<InventoryOrder[]> {
  const res = await authedFetch(`${apiBase()}/inventory/orders`, {
    cache: "no-store",
  });
  const rows = await readResponseJson<Record<string, unknown>[]>(res);
  return rows.map(asOrder);
}
