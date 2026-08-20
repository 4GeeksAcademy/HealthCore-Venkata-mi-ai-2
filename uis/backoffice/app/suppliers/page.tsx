import { SupplierDirectoryPanel } from "@/components/suppliers/SupplierDirectoryPanel";

export default function SuppliersPage() {
  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Procurement</p>
          <h1>Supplier directory</h1>
          <p>
            Internal clinic supplier registry for USA and UK outpatient sites.
            Monthly rates and activation status are managed here for Clinical
            Operations procurement.
          </p>
        </section>
        <SupplierDirectoryPanel />
      </div>
    </main>
  );
}
