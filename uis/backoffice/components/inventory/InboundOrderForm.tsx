"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AsyncState } from "@/components/async/AsyncState";
import {
  createInboundOrder,
  fetchInventoryProducts,
} from "@/lib/inventory-api";
import { getUserFacingError } from "@/lib/user-facing-error";
import type { InventoryProduct } from "@/types/inventory";

export function InboundOrderForm() {
  const router = useRouter();
  const [products, setProducts] = useState<InventoryProduct[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [productId, setProductId] = useState("");
  const [quantity, setQuantity] = useState("");
  const [notes, setNotes] = useState("");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await fetchInventoryProducts();
      setProducts(data);
      setProductId((current) => current || (data[0] ? String(data[0].id) : ""));
    } catch (err) {
      setLoadError(
        getUserFacingError(err, "Unable to load products. Please try again."),
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
          setProductId((current) =>
            current || (data[0] ? String(data[0].id) : ""),
          );
        }
      } catch (err) {
        if (!cancelled) {
          setLoadError(
            getUserFacingError(
              err,
              "Unable to load products. Please try again.",
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

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    const parsedProductId = Number(productId);
    const parsedQuantity = Number(quantity);
    if (!Number.isInteger(parsedProductId) || parsedProductId <= 0) {
      setFormError("Select a product.");
      return;
    }
    if (!Number.isInteger(parsedQuantity) || parsedQuantity <= 0) {
      setFormError("Quantity must be a whole number greater than zero.");
      return;
    }

    setSubmitting(true);
    try {
      await createInboundOrder({
        product_id: parsedProductId,
        quantity: parsedQuantity,
        notes: notes.trim(),
      });
      router.push("/inventory?notice=inbound");
    } catch (err) {
      setFormError(
        getUserFacingError(
          err,
          "Unable to register the inbound order. Please try again.",
        ),
      );
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AsyncState
      loading={loading}
      error={loadError}
      onRetry={() => void load()}
      loadingText="Loading products…"
      isEmpty={products.length === 0}
      emptyState={
        <p className="muted-text">
          No products available. Seed inventory before logging a delivery.
        </p>
      }
    >
      <form className="stack" onSubmit={(event) => void onSubmit(event)}>
        <div className="field-grid">
          <div className="field">
            <label htmlFor="inbound-product">Product</label>
            <select
              id="inbound-product"
              value={productId}
              onChange={(event) => setProductId(event.target.value)}
              required
            >
              {products.map((product) => (
                <option key={product.id} value={product.id}>
                  {product.name} ({product.sku})
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="inbound-quantity">Quantity</label>
            <input
              id="inbound-quantity"
              type="number"
              min={1}
              step={1}
              value={quantity}
              onChange={(event) => setQuantity(event.target.value)}
              required
            />
          </div>
        </div>
        <div className="field">
          <label htmlFor="inbound-notes">Notes</label>
          <textarea
            id="inbound-notes"
            value={notes}
            onChange={(event) => setNotes(event.target.value)}
            rows={3}
          />
        </div>
        {formError ? (
          <p className="feedback error" role="alert">
            {formError}
          </p>
        ) : null}
        <div className="inline-actions">
          <button type="submit" className="link-button" disabled={submitting}>
            {submitting ? "Saving…" : "Register inbound delivery"}
          </button>
        </div>
      </form>
    </AsyncState>
  );
}
