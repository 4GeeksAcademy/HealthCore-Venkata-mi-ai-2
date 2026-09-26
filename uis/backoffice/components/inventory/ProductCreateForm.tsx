"use client";

import { FormEvent, useState } from "react";
import { createMedicalSupply } from "@/lib/inventory-api";
import { getUserFacingError } from "@/lib/user-facing-error";

export function ProductCreateForm({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [sku, setSku] = useState("");
  const [threshold, setThreshold] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    const parsedThreshold = Number(threshold);
    if (!name.trim() || !sku.trim() || !Number.isInteger(parsedThreshold) || parsedThreshold < 0) {
      setError("Enter a name, SKU, and a threshold of zero or more.");
      return;
    }
    setBusy(true);
    try {
      await createMedicalSupply({
        name: name.trim(),
        sku: sku.trim(),
        threshold: parsedThreshold,
      });
      setName("");
      setSku("");
      setThreshold("");
      onCreated();
    } catch (err) {
      setError(getUserFacingError(err, "Unable to add the supply. Please try again."));
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="stack" onSubmit={(event) => void onSubmit(event)}>
      <div className="field-grid">
        <div className="field">
          <label htmlFor="supply-name">Name</label>
          <input id="supply-name" value={name} onChange={(e) => setName(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="supply-sku">SKU</label>
          <input id="supply-sku" value={sku} onChange={(e) => setSku(e.target.value)} required />
        </div>
        <div className="field">
          <label htmlFor="supply-threshold">Threshold</label>
          <input
            id="supply-threshold"
            inputMode="numeric"
            value={threshold}
            onChange={(e) => setThreshold(e.target.value)}
            required
          />
        </div>
      </div>
      {error ? (
        <div className="feedback error" role="alert">
          <p>{error}</p>
          <button type="button" className="link-button secondary" onClick={() => setError(null)}>
            Dismiss
          </button>
        </div>
      ) : null}
      <button type="submit" className="button" disabled={busy}>
        {busy ? "Saving…" : "Add supply"}
      </button>
    </form>
  );
}
