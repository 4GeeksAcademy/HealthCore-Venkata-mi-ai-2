"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ErrorActions } from "@/components/async/ErrorActions";
import { authedFetch } from "@/lib/authed-fetch";

type ClinicRow = {
  clinic_id: string;
  country: string;
  total_supply_cost: number;
  supply_consumption_count: number;
  critical_stockout_count: number;
  expiry_risk_count: number;
  currency: string;
};

type MonthlyBody = {
  month_start: string;
  clinics: ClinicRow[];
};

function formatMoney(amount: number, currency: string): string {
  try {
    return new Intl.NumberFormat(undefined, {
      style: "currency",
      currency,
      maximumFractionDigits: 2,
    }).format(amount);
  } catch {
    return `${amount.toFixed(2)} ${currency}`;
  }
}

export default function MonthlyClinicSupplyReportingPage() {
  const [report, setReport] = useState<MonthlyBody | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await authedFetch(
        "/reporting/monthly-clinic-supply-performance",
      );
      if (!response.ok) {
        throw new Error("unavailable");
      }
      const body = (await response.json()) as MonthlyBody;
      setReport(body);
    } catch {
      setReport(null);
      setError("The monthly clinic supply report could not be loaded.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const handle = window.setTimeout(() => {
      void load();
    }, 0);
    return () => window.clearTimeout(handle);
  }, [load]);

  const clinics = report?.clinics ?? [];

  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Leadership</p>
          <h1>Monthly Clinic Supply Performance</h1>
          <p>
            Clinic-by-clinic supply pack for Dr. Okonkwo and Claire: purchase
            cost, consumption volume, critical stockouts, and expiry risk for
            one calendar month.
          </p>
          <p>
            Period (month starting):{" "}
            <strong>{report?.month_start ?? "…"}</strong>
          </p>
          <div className="inline-actions">
            <Link className="link-button secondary" href="/" prefetch={false}>
              Back to welcome
            </Link>
          </div>
        </section>

        {loading ? (
          <section className="section-card">
            <p className="muted-text" role="status">
              Loading monthly clinic supply performance…
            </p>
          </section>
        ) : null}

        {error ? (
          <section className="section-card" role="alert">
            <p>{error}</p>
            <ErrorActions onRetry={() => void load()} />
          </section>
        ) : null}

        {!loading && !error && clinics.length === 0 ? (
          <section className="section-card">
            <p className="muted-text">
              No clinic rows yet for this month. Run the supply performance
              pipeline, then refresh.
            </p>
          </section>
        ) : null}

        {!loading && !error && clinics.length > 0 ? (
          <>
            <section className="section-card">
              <h2>Supply Cost per Clinic</h2>
              <p className="muted-text">
                Sum of inbound order costs for the month (USD and GBP shown in
                each clinic&apos;s currency; not converted).
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Clinic</th>
                      <th scope="col">Country</th>
                      <th scope="col">Supply Cost per Clinic</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clinics.map((row) => (
                      <tr key={`cost-${row.clinic_id}`}>
                        <td>{row.clinic_id}</td>
                        <td>{row.country}</td>
                        <td>
                          {formatMoney(row.total_supply_cost, row.currency)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="section-card">
              <h2>Supply Consumption Volume</h2>
              <p className="muted-text">
                Number of outbound supply orders recorded in the month.
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Clinic</th>
                      <th scope="col">Country</th>
                      <th scope="col">Supply Consumption Volume</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clinics.map((row) => (
                      <tr key={`cons-${row.clinic_id}`}>
                        <td>{row.clinic_id}</td>
                        <td>{row.country}</td>
                        <td>{row.supply_consumption_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="section-card">
              <h2>Critical Stockout Frequency</h2>
              <p className="muted-text">
                How often stock crossed under the minimum threshold.
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Clinic</th>
                      <th scope="col">Country</th>
                      <th scope="col">Critical Stockout Frequency</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clinics.map((row) => (
                      <tr key={`stock-${row.clinic_id}`}>
                        <td>{row.clinic_id}</td>
                        <td>{row.country}</td>
                        <td>{row.critical_stockout_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>

            <section className="section-card">
              <h2>Expiry Risk Count</h2>
              <p className="muted-text">
                Batches flagged as nearing expiry during the month.
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Clinic</th>
                      <th scope="col">Country</th>
                      <th scope="col">Expiry Risk Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {clinics.map((row) => (
                      <tr key={`exp-${row.clinic_id}`}>
                        <td>{row.clinic_id}</td>
                        <td>{row.country}</td>
                        <td>{row.expiry_risk_count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          </>
        ) : null}
      </div>
    </main>
  );
}
