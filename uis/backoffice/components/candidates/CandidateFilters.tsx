"use client";

import { FormEvent } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { candidateStageOptions, candidateStatusOptions } from "@/types/candidate";
import { branding } from "@/lib/branding";

export function CandidateFilters() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const status = searchParams.get("status") ?? "";
  const stage = searchParams.get("stage") ?? "";
  const query = searchParams.get("query") ?? "";
  const limit = searchParams.get("limit") ?? "20";

  function updateParams(updates: Record<string, string>) {
    const params = new URLSearchParams(searchParams.toString());

    Object.entries(updates).forEach(([key, value]) => {
      if (value) {
        params.set(key, value);
      } else {
        params.delete(key);
      }
    });

    if (["status", "stage", "query", "limit"].some((key) => key in updates)) {
      params.delete("page");
    }

    const nextQuery = params.toString();
    router.replace(nextQuery ? `${pathname}?${nextQuery}` : pathname);
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const nextQuery = String(formData.get("candidate-query") ?? "").trim();

    updateParams({ query: nextQuery });
  }

  return (
    <section className="section-card filter-panel">
      <header>
        <h2>Search and filters</h2>
        <p>
          Filter {branding.candidatePlural.toLowerCase()} by {branding.statusLabel.toLowerCase()},{" "}
          {branding.stageLabel.toLowerCase()}, or search by name and email.
        </p>
      </header>

      <form key={query} className="stack" onSubmit={handleSubmit}>
        <div className="filter-grid">
          <div className="field field-span-2">
            <label htmlFor="candidate-query">Search</label>
            <input
              id="candidate-query"
              name="candidate-query"
              defaultValue={query}
              placeholder="Search by full name or email"
            />
          </div>

          <div className="field">
            <label htmlFor="status-filter">{branding.statusLabel}</label>
            <div className="select-wrap">
              <select
                id="status-filter"
                name="status-filter"
                value={status}
                onChange={(event) => updateParams({ status: event.target.value })}
              >
                <option value="">All statuses</option>
                {candidateStatusOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="field">
            <label htmlFor="stage-filter">{branding.stageLabel}</label>
            <div className="select-wrap">
              <select
                id="stage-filter"
                name="stage-filter"
                value={stage}
                onChange={(event) => updateParams({ stage: event.target.value })}
              >
                <option value="">All stages</option>
                {candidateStageOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="field">
            <label htmlFor="limit-filter">Results per page</label>
            <div className="select-wrap">
              <select
                id="limit-filter"
                name="limit-filter"
                value={limit}
                onChange={(event) => updateParams({ limit: event.target.value })}
              >
                <option value="20">20</option>
                <option value="50">50</option>
                <option value="100">100</option>
              </select>
            </div>
          </div>
        </div>

        <div className="button-row filter-actions">
          <button className="button" type="submit">
            Apply search
          </button>
          <button
            className="button ghost"
            type="button"
            onClick={() => router.replace(pathname)}
          >
            Clear filters
          </button>
        </div>
      </form>
    </section>
  );
}