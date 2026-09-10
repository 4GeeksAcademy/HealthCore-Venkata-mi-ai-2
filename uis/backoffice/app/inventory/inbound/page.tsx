import { InventoryNav } from "@/components/inventory/InventoryNav";
import { InboundOrderForm } from "@/components/inventory/InboundOrderForm";

export default function InventoryInboundPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Clinical operations</p>
          <h1>Register inbound delivery</h1>
          <p>
            Log a delivery received at a clinic. A confirmation is shown after
            a successful save, then you return to the stock list.
          </p>
        </section>
        <section className="section-card">
          <InventoryNav current="/inventory/inbound" />
        </section>
        <section className="section-card">
          <header>
            <h2>Inbound order</h2>
            <p className="muted-text">Product, quantity, and notes.</p>
          </header>
          <InboundOrderForm />
        </section>
      </div>
    </main>
  );
}
