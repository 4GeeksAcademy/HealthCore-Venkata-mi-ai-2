import { InventoryNav } from "@/components/inventory/InventoryNav";
import { OutboundOrderForm } from "@/components/inventory/OutboundOrderForm";

export default function InventoryOutboundPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Clinical operations</p>
          <h1>Register outbound order</h1>
          <p>
            Log consumption or an exit. Available stock for the selected
            product is shown before you enter a quantity.
          </p>
        </section>
        <section className="section-card">
          <InventoryNav current="/inventory/outbound" />
        </section>
        <section className="section-card">
          <header>
            <h2>Outbound order</h2>
            <p className="muted-text">
              Available stock updates when the product selection changes.
            </p>
          </header>
          <OutboundOrderForm />
        </section>
      </div>
    </main>
  );
}
