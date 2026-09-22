import { isLowStock, type InventoryProduct } from "@/types/inventory";

export type StockInsights = {
  total: number;
  lowCount: number;
  okCount: number;
  unitsBelowThreshold: number;
  lowStock: InventoryProduct[];
};

/** Rank clinic supplies that are below restock threshold by unit deficit. */
export function buildStockInsights(products: InventoryProduct[]): StockInsights {
  const lowStock = products
    .filter((product) => isLowStock(product))
    .map((product) => product)
    .sort((left, right) => {
      const deficitLeft = left.threshold - left.stock;
      const deficitRight = right.threshold - right.stock;
      if (deficitRight !== deficitLeft) {
        return deficitRight - deficitLeft;
      }
      return left.name.localeCompare(right.name);
    });

  return {
    total: products.length,
    lowCount: lowStock.length,
    okCount: products.length - lowStock.length,
    unitsBelowThreshold: lowStock.reduce(
      (sum, product) => sum + (product.threshold - product.stock),
      0,
    ),
    lowStock,
  };
}
