import { InventoryNav } from "@/components/inventory/InventoryNav";
import { OrderHistoryPanel } from "@/components/inventory/OrderHistoryPanel";

export default function InventoryOrdersPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Clinical operations</p>
          <h1>Order history</h1>
          <p>
            Read-only list of inbound deliveries and outbound exits, including
            who created each order.
          </p>
        </section>
        <section className="section-card">
          <InventoryNav current="/inventory/orders" />
        </section>
        <section className="section-card">
          <header>
            <h2>All orders</h2>
            <p className="muted-text">
              Product name, type, quantity, date, and creator.
            </p>
          </header>
          <OrderHistoryPanel />
        </section>
      </div>
    </main>
  );
}
