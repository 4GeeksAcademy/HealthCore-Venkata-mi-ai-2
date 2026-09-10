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

export async function fetchInventoryProducts(): Promise<InventoryProduct[]> {
  const res = await authedFetch(`${apiBase()}/inventory/products`, {
    cache: "no-store",
  });
  return readResponseJson<InventoryProduct[]>(res);
}

export async function createInboundOrder(
  payload: InventoryOrderCreate,
): Promise<InventoryOrder> {
  const res = await authedFetch(`${apiBase()}/inventory/inbound`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readResponseJson<InventoryOrder>(res);
}

export async function createOutboundOrder(
  payload: InventoryOrderCreate,
): Promise<InventoryOrder> {
  const res = await authedFetch(`${apiBase()}/inventory/outbound`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return readResponseJson<InventoryOrder>(res);
}

export async function fetchInventoryOrders(): Promise<InventoryOrder[]> {
  const res = await authedFetch(`${apiBase()}/inventory/orders`, {
    cache: "no-store",
  });
  return readResponseJson<InventoryOrder[]>(res);
}
