export type InventoryOrderType = "inbound" | "outbound";

export interface InventoryProduct {
  id: number;
  name: string;
  sku: string;
  stock: number;
  threshold: number;
}

export interface InventoryOrder {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  type: InventoryOrderType;
  notes: string;
  created_at: string;
  created_by: string;
}

export interface InventoryOrderCreate {
  product_id: number;
  quantity: number;
  notes: string;
}

export function isLowStock(product: InventoryProduct): boolean {
  return product.stock < product.threshold;
}
