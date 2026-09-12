"use client";

import { useCallback, useEffect, useState } from "react";
import { AsyncState } from "@/components/async/AsyncState";
import { fetchInventoryOrders } from "@/lib/inventory-api";
import { getUserFacingError } from "@/lib/user-facing-error";
import type { InventoryOrder } from "@/types/inventory";

function formatWhen(value: string): string {
  const parsed = Date.parse(value);
  if (Number.isNaN(parsed)) {
    return value || "—";
  }
  return new Date(parsed).toLocaleString();
}

export function OrderHistoryPanel() {
  const [orders, setOrders] = useState<InventoryOrder[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchInventoryOrders();
      setOrders(data);
    } catch (err) {
      setError(
        getUserFacingError(err, "Unable to load orders. Please try again."),
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await fetchInventoryOrders();
        if (!cancelled) {
          setOrders(data);
        }
      } catch (err) {
        if (!cancelled) {
          setError(
            getUserFacingError(err, "Unable to load orders. Please try again."),
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

  return (
    <AsyncState
      loading={loading}
      error={error}
      onRetry={() => void load()}
      loadingText="Loading order history…"
      isEmpty={orders.length === 0}
      emptyState={
        <p className="muted-text">
          No inbound or outbound orders have been recorded yet.
        </p>
      }
    >
      <div style={{ overflowX: "auto" }}>
        <table className="data-table">
          <thead>
            <tr>
              <th>Product</th>
              <th>Type</th>
              <th>Quantity</th>
              <th>Date</th>
              <th>Created by</th>
            </tr>
          </thead>
          <tbody>
            {orders.map((order) => (
              <tr key={`${order.type}-${order.id}`}>
                <td>{order.product_name}</td>
                <td>
                  <span
                    className={
                      order.type === "inbound"
                        ? "pill stock-ok"
                        : "pill stock-low"
                    }
                  >
                    {order.type}
                  </span>
                </td>
                <td>{order.quantity}</td>
                <td>{formatWhen(order.created_at)}</td>
                <td>{order.created_by}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </AsyncState>
  );
}
