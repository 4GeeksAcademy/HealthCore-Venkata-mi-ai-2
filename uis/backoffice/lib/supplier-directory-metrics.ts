import type { ProductCategory, Supplier } from "@/types/supplier";
import { PRODUCT_CATEGORIES } from "@/types/supplier";

export type SupplierDirectorySummary = {
  total: number;
  activeCount: number;
  suspendedCount: number;
  usaMonthlyUsd: number;
  ukMonthlyGbp: number;
  categoryCounts: Record<ProductCategory, number>;
};

function emptyCategoryCounts(): Record<ProductCategory, number> {
  return PRODUCT_CATEGORIES.reduce(
    (counts, category) => {
      counts[category] = 0;
      return counts;
    },
    {} as Record<ProductCategory, number>,
  );
}

/** Aggregate directory spend and status. Re-run only when the supplier list changes. */
export function summarizeSupplierDirectory(
  suppliers: Supplier[],
): SupplierDirectorySummary {
  const categoryCounts = emptyCategoryCounts();
  let activeCount = 0;
  let suspendedCount = 0;
  let usaMonthlyUsd = 0;
  let ukMonthlyGbp = 0;

  for (const supplier of suppliers) {
    if (supplier.status === "active") {
      activeCount += 1;
    } else {
      suspendedCount += 1;
    }
    if (supplier.currency === "USD") {
      usaMonthlyUsd += supplier.monthly_rate;
    } else {
      ukMonthlyGbp += supplier.monthly_rate;
    }
    for (const category of supplier.categories) {
      categoryCounts[category] += 1;
    }
  }

  return {
    total: suppliers.length,
    activeCount,
    suspendedCount,
    usaMonthlyUsd,
    ukMonthlyGbp,
    categoryCounts,
  };
}
