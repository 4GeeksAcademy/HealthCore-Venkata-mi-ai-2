import { summarizeSupplierDirectory } from "@/lib/supplier-directory-metrics";
import type { Supplier } from "@/types/supplier";

function vendor(
  overrides: Partial<Supplier> & Pick<Supplier, "id" | "name">,
): Supplier {
  return {
    country: "USA",
    categories: ["PPE"],
    monthly_rate: 100,
    currency: "USD",
    updated_at: "2026-09-21T00:00:00+00:00",
    status: "active",
    ...overrides,
  };
}

describe("summarizeSupplierDirectory", () => {
  test("aggregates spend, status, and overlapping categories", () => {
    const summary = summarizeSupplierDirectory([
      vendor({
        id: 1,
        name: "Austin PPE",
        monthly_rate: 200,
        categories: ["PPE", "MEDICAL_SUPPLIES"],
      }),
      vendor({
        id: 2,
        name: "London Labs",
        country: "UK",
        currency: "GBP",
        monthly_rate: 50,
        categories: ["LAB_CONSUMABLES"],
        status: "suspended",
      }),
    ]);

    expect(summary.total).toBe(2);
    expect(summary.activeCount).toBe(1);
    expect(summary.suspendedCount).toBe(1);
    expect(summary.usaMonthlyUsd).toBe(200);
    expect(summary.ukMonthlyGbp).toBe(50);
    expect(summary.categoryCounts.PPE).toBe(1);
    expect(summary.categoryCounts.MEDICAL_SUPPLIES).toBe(1);
    expect(summary.categoryCounts.LAB_CONSUMABLES).toBe(1);
  });
});
