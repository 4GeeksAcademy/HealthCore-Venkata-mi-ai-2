"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { AsyncState } from "@/components/async/AsyncState";
import { ProductCreateForm } from "@/components/inventory/ProductCreateForm";
import { fetchInventoryProducts } from "@/lib/inventory-api";
import { buildStockInsights } from "@/lib/inventory-stock-metrics";
import { getUserFacingError } from "@/lib/user-facing-error";
import { isLowStock, type InventoryProduct } from "@/types/inventory";

export function ProductStockPanel() {
  const searchParams = useSearchParams();
  const notice = searchParams.get("notice");
  const [products, setProducts] = useState<InventoryProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInventoryProducts();
      setProducts(data);
    } catch (err) {
      setError(
        getUserFacingError(err, "Unable to load inventory. Please try again."),
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchInventoryProducts();
        if (!cancelled) {
          setProducts(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            getUserFacingError(
              err,
              "Unable to load inventory. Please try again.",
            ),
          );
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const stockInsights = useMemo(
    () => buildStockInsights(products),
    [products],
  );

  return (
    <div className="stack">
      {notice === "inbound" ? (
        <p className="feedback info" role="status">
          Inbound delivery registered. Stock below is the current available
          quantity.
        </p>
      ) : null}

      <ProductCreateForm onCreated={() => void load()} />

      <AsyncState
        loading={loading}
        error={error}
        onRetry={() => void load()}
        loadingText="Loading clinic stock…"
        isEmpty={products.length === 0}
        emptyState={
          <p className="muted-text">
            No products in inventory yet. Register an inbound delivery after
            the catalog is seeded.
          </p>
        }
      >
        <>
          {stockInsights.lowCount > 0 ? (
            <p className="muted-text">
              {stockInsights.lowCount} of {stockInsights.total} SKUs are below
              threshold ({stockInsights.unitsBelowThreshold} units short). Highest
              deficit: {stockInsights.lowStock[0]?.name ?? "n/a"}.
            </p>
          ) : (
            <p className="muted-text">
              All {stockInsights.total} SKUs are at or above threshold.
            </p>
          )}
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>SKU</th>
                  <th>Current stock</th>
                  <th>Threshold</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {products.map((product) => {
                  const low = isLowStock(product);
                  return (
                    <tr key={product.id}>
                      <td>{product.name}</td>
                      <td>{product.sku}</td>
                      <td>{product.stock}</td>
                      <td>{product.threshold}</td>
                      <td>
                        <span
                          className={low ? "pill stock-low" : "pill stock-ok"}
                        >
                          {low ? "Low stock" : "In stock"}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </>
      </AsyncState>
    </div>
  );
}
