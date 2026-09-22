import { buildStockInsights } from "@/lib/inventory-stock-metrics";
import type { InventoryProduct } from "@/types/inventory";

function product(
  overrides: Partial<InventoryProduct> & Pick<InventoryProduct, "id" | "name">,
): InventoryProduct {
  return {
    sku: `HC-${overrides.id}`,
    stock: 10,
    threshold: 10,
    ...overrides,
  };
}

describe("buildStockInsights", () => {
  test("sorts low-stock rows by deficit and sums units below threshold", () => {
    const insights = buildStockInsights([
      product({ id: 1, name: "Gloves", stock: 8, threshold: 12 }),
      product({ id: 2, name: "Pads", stock: 40, threshold: 30 }),
      product({ id: 3, name: "Masks", stock: 1, threshold: 10 }),
    ]);

    expect(insights.total).toBe(3);
    expect(insights.lowCount).toBe(2);
    expect(insights.okCount).toBe(1);
    expect(insights.unitsBelowThreshold).toBe(13);
    expect(insights.lowStock.map((row) => row.name)).toEqual(["Masks", "Gloves"]);
  });
});
