import { ApiError } from "@/lib/authed-fetch";
import { track } from "@/lib/telemetry";

export function trackInventoryFailure(
  route:
    | "POST /inventory/products"
    | "POST /inventory/orders/inbound"
    | "POST /inventory/orders/outbound",
  err: unknown,
  fields: { product_id?: number; sku?: string; quantity?: number },
): void {
  const message = err instanceof Error ? err.message : "";
  const status = err instanceof ApiError ? err.status : 422;
  let reason = "validation_error";
  const properties: Record<string, unknown> = {
    reason,
    status_code: status,
    route,
  };
  if (fields.product_id) properties.product_id = fields.product_id;
  if (fields.sku) properties.sku = fields.sku;
  if (fields.quantity) properties.quantity = fields.quantity;
  if (message === "SKU already exists.") reason = "duplicate_sku";
  if (message === "Product not found.") reason = "product_not_found";
  const available = message.match(/Available: (\d+)\./);
  if (available) {
    reason = "insufficient_stock";
    properties.available_stock = Number(available[1]);
  }
  properties.reason = reason;
  if (status !== 400 && status !== 404 && status !== 422) return;
  track("order_validation_failed", properties);
}
