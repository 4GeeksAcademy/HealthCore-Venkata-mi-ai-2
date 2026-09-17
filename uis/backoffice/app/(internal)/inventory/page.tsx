import { Suspense } from "react";
import { InventoryNav } from "@/components/inventory/InventoryNav";
import { ProductStockPanel } from "@/components/inventory/ProductStockPanel";

export default function InventoryStockPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Clinical operations</p>
          <h1>Clinic inventory</h1>
          <p>
            Current stock for outpatient clinic supplies. Low stock is
            highlighted when quantity is below the restock threshold.
          </p>
        </section>
        <section className="section-card">
          <InventoryNav current="/inventory" />
        </section>
        <section className="section-card">
          <header>
            <h2>Products</h2>
            <p className="muted-text">
              Name, SKU, current stock, and threshold from the live inventory
              API.
            </p>
          </header>
          <Suspense
            fallback={
              <p className="muted-text" role="status">
                Loading clinic stock…
              </p>
            }
          >
            <ProductStockPanel />
          </Suspense>
        </section>
      </div>
    </main>
  );
}
