"use client";

import { FormEvent, useCallback, useEffect, useMemo, useState } from "react";
import {
  createSupplier,
  fetchSuppliers,
  updateSupplierRate,
  updateSupplierStatus,
} from "@/lib/suppliers-api";
import {
  PRODUCT_CATEGORIES,
  type ProductCategory,
  type Supplier,
  type SupplierCountry,
  type SupplierStatus,
} from "@/types/supplier";

const COUNTRIES: SupplierCountry[] = ["US", "UK"];
const STATUSES: SupplierStatus[] = ["active", "suspended"];

export function SupplierDirectoryPanel() {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [countryFilter, setCountryFilter] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");

  const [name, setName] = useState("");
  const [country, setCountry] = useState<SupplierCountry>("US");
  const [categories, setCategories] = useState<ProductCategory[]>([]);
  const [contractRate, setContractRate] = useState("");
  const [status, setStatus] = useState<SupplierStatus>("active");
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const [rateDrafts, setRateDrafts] = useState<Record<number, string>>({});
  const [rowBusy, setRowBusy] = useState<Record<number, boolean>>({});
  const [rowError, setRowError] = useState<Record<number, string>>({});

  const load = useCallback(async () => {
    setLoading(true);
    setLoadError(null);
    try {
      const data = await fetchSuppliers({
        country: countryFilter || undefined,
        category: categoryFilter || undefined,
      });
      setSuppliers(data);
      setRateDrafts(
        Object.fromEntries(data.map((s) => [s.id, String(s.contract_rate)])),
      );
    } catch (err) {
      setLoadError(err instanceof Error ? err.message : "Failed to load suppliers.");
    } finally {
      setLoading(false);
    }
  }, [countryFilter, categoryFilter]);

  useEffect(() => {
    void load();
  }, [load]);

  const categoryOptions = useMemo(() => PRODUCT_CATEGORIES, []);

  function toggleCategory(cat: ProductCategory) {
    setCategories((prev) =>
      prev.includes(cat) ? prev.filter((c) => c !== cat) : [...prev, cat],
    );
  }

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    setFormError(null);

    const trimmed = name.trim();
    const rate = Number(contractRate);
    if (!trimmed) {
      setFormError("Name is required.");
      return;
    }
    if (!COUNTRIES.includes(country)) {
      setFormError("Country must be US or UK.");
      return;
    }
    if (categories.length === 0) {
      setFormError("Select at least one product category.");
      return;
    }
    if (!Number.isFinite(rate) || rate <= 0) {
      setFormError("Contract rate must be a number greater than zero.");
      return;
    }
    if (!STATUSES.includes(status)) {
      setFormError("Status must be active or suspended.");
      return;
    }

    setSubmitting(true);
    try {
      await createSupplier({
        name: trimmed,
        country,
        product_categories: categories,
        contract_rate: rate,
        status,
      });
      setName("");
      setCategories([]);
      setContractRate("");
      setStatus("active");
      await load();
    } catch (err) {
      setFormError(err instanceof Error ? err.message : "Create failed.");
    } finally {
      setSubmitting(false);
    }
  }

  async function onSaveRate(id: number) {
    const rate = Number(rateDrafts[id]);
    if (!Number.isFinite(rate) || rate <= 0) {
      setRowError((prev) => ({
        ...prev,
        [id]: "Contract rate must be greater than zero.",
      }));
      return;
    }
    setRowBusy((prev) => ({ ...prev, [id]: true }));
    setRowError((prev) => ({ ...prev, [id]: "" }));
    try {
      const updated = await updateSupplierRate(id, rate);
      setSuppliers((prev) => prev.map((s) => (s.id === id ? updated : s)));
      setRateDrafts((prev) => ({ ...prev, [id]: String(updated.contract_rate) }));
    } catch (err) {
      setRowError((prev) => ({
        ...prev,
        [id]: err instanceof Error ? err.message : "Rate update failed.",
      }));
    } finally {
      setRowBusy((prev) => ({ ...prev, [id]: false }));
    }
  }

  async function onToggleStatus(supplier: Supplier) {
    const next: SupplierStatus =
      supplier.status === "active" ? "suspended" : "active";
    setRowBusy((prev) => ({ ...prev, [supplier.id]: true }));
    setRowError((prev) => ({ ...prev, [supplier.id]: "" }));
    try {
      const updated = await updateSupplierStatus(supplier.id, next);
      setSuppliers((prev) =>
        prev.map((s) => (s.id === supplier.id ? updated : s)),
      );
    } catch (err) {
      setRowError((prev) => ({
        ...prev,
        [supplier.id]:
          err instanceof Error ? err.message : "Status update failed.",
      }));
    } finally {
      setRowBusy((prev) => ({ ...prev, [supplier.id]: false }));
    }
  }

  return (
    <div className="stack">
      <section className="section-card">
        <header>
          <h2>Filters</h2>
          <p className="muted-text">
            Country and category filters update the list without reloading the page.
          </p>
        </header>
        <div className="controls-grid">
          <div className="field">
            <label htmlFor="filter-country">Country</label>
            <select
              id="filter-country"
              value={countryFilter}
              onChange={(e) => setCountryFilter(e.target.value)}
            >
              <option value="">All countries</option>
              {COUNTRIES.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
          <div className="field">
            <label htmlFor="filter-category">Category</label>
            <select
              id="filter-category"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="">All categories</option>
              {categoryOptions.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
          </div>
        </div>
      </section>

      <section className="section-card">
        <header>
          <h2>Register supplier</h2>
          <p className="muted-text">
            Required: name, country, categories, contract_rate (&gt; 0), status.
          </p>
        </header>
        <form className="stack" onSubmit={onCreate}>
          <div className="field-grid">
            <div className="field">
              <label htmlFor="supplier-name">Name</label>
              <input
                id="supplier-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="supplier-country">Country</label>
              <select
                id="supplier-country"
                value={country}
                onChange={(e) => setCountry(e.target.value as SupplierCountry)}
              >
                {COUNTRIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>
            <div className="field">
              <label htmlFor="supplier-rate">Contract rate (USD)</label>
              <input
                id="supplier-rate"
                type="number"
                min="0.01"
                step="0.01"
                value={contractRate}
                onChange={(e) => setContractRate(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="supplier-status">Status</label>
              <select
                id="supplier-status"
                value={status}
                onChange={(e) => setStatus(e.target.value as SupplierStatus)}
              >
                {STATUSES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
          </div>
          <fieldset className="field">
            <legend>Product categories</legend>
            <div className="inline-actions">
              {categoryOptions.map((cat) => (
                <label key={cat} className="pill" style={{ cursor: "pointer" }}>
                  <input
                    type="checkbox"
                    checked={categories.includes(cat)}
                    onChange={() => toggleCategory(cat)}
                    style={{ marginRight: "0.4rem" }}
                  />
                  {cat}
                </label>
              ))}
            </div>
          </fieldset>
          {formError ? <p className="status-text" style={{ color: "var(--danger)" }}>{formError}</p> : null}
          <div className="inline-actions">
            <button type="submit" className="link-button" disabled={submitting}>
              {submitting ? "Saving…" : "Create supplier"}
            </button>
          </div>
        </form>
      </section>

      <section className="section-card">
        <header>
          <h2>Supplier directory</h2>
          <p className="muted-text">
            Fields from CONTEXT: name, country, product_categories, contract_rate, status.
          </p>
        </header>
        {loading ? <p className="muted-text">Loading…</p> : null}
        {loadError ? (
          <p className="status-text" style={{ color: "var(--danger)" }}>
            {loadError}
          </p>
        ) : null}
        {!loading && !loadError && suppliers.length === 0 ? (
          <p className="muted-text">No suppliers match the current filters.</p>
        ) : null}
        {suppliers.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Country</th>
                  <th>Categories</th>
                  <th>Contract rate</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {suppliers.map((supplier) => {
                  const busy = Boolean(rowBusy[supplier.id]);
                  return (
                    <tr key={supplier.id}>
                      <td>{supplier.name}</td>
                      <td>{supplier.country}</td>
                      <td>{supplier.product_categories.join(", ")}</td>
                      <td>
                        <div className="inline-actions">
                          <input
                            type="number"
                            min="0.01"
                            step="0.01"
                            value={rateDrafts[supplier.id] ?? ""}
                            onChange={(e) =>
                              setRateDrafts((prev) => ({
                                ...prev,
                                [supplier.id]: e.target.value,
                              }))
                            }
                            style={{ width: "6.5rem" }}
                            disabled={busy}
                          />
                          <button
                            type="button"
                            className="link-button secondary"
                            disabled={busy}
                            onClick={() => void onSaveRate(supplier.id)}
                          >
                            Save rate
                          </button>
                        </div>
                      </td>
                      <td>
                        <span
                          className={
                            supplier.status === "active"
                              ? "pill supplier-status-active"
                              : "pill supplier-status-suspended"
                          }
                        >
                          {supplier.status}
                        </span>
                      </td>
                      <td>
                        <button
                          type="button"
                          className="link-button secondary"
                          disabled={busy}
                          onClick={() => void onToggleStatus(supplier)}
                        >
                          {supplier.status === "active" ? "Suspend" : "Activate"}
                        </button>
                        {rowError[supplier.id] ? (
                          <p
                            className="status-text"
                            style={{ color: "var(--danger)", marginTop: "0.4rem" }}
                          >
                            {rowError[supplier.id]}
                          </p>
                        ) : null}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : null}
      </section>
    </div>
  );
}
