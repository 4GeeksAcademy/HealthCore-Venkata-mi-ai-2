"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AsyncState } from "@/components/async/AsyncState";
import { CandidateFilters } from "@/components/candidates/CandidateFilters";
import { CandidateForm } from "@/components/candidates/CandidateForm";
import { CandidateTable } from "@/components/candidates/CandidateTable";
import { getErrorMessage } from "@/lib/api-client";
import { branding } from "@/lib/branding";
import {
  createRecord,
  getDefaultCandidateValues,
  getRecords,
  RecordsResult,
} from "@/lib/records-service";
import { AsyncDataState } from "@/types/api";
import { useSearchParams } from "next/navigation";

const DEFAULT_PAGE_SIZE = 20;

export function CandidateListPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const query = searchParams.get("query") ?? "";
  const status = searchParams.get("status") ?? "";
  const stage = searchParams.get("stage") ?? "";
  const page = sanitizePositiveInteger(searchParams.get("page"), 1);
  const limit = sanitizePositiveInteger(searchParams.get("limit"), DEFAULT_PAGE_SIZE);
  const hasActiveFilters = Boolean(query || status || stage);
  const [createFormVersion, setCreateFormVersion] = useState(0);
  const [refreshKey, setRefreshKey] = useState(0);
  const [recordsState, setRecordsState] = useState<AsyncDataState<RecordsResult>>({
    loading: true,
    error: null,
    data: null,
  });
  const records = recordsState.data?.records ?? [];
  const total = recordsState.data?.total ?? 0;
  const currentPage = recordsState.data?.page ?? page;
  const currentLimit = recordsState.data?.limit ?? limit;
  const totalPages = Math.max(1, Math.ceil(total / currentLimit));

  useEffect(() => {
    let active = true;

    async function loadRecords() {
      try {
        setRecordsState({ loading: true, error: null, data: null });
        const result = await getRecords({
          query,
          status,
          stage,
          page: String(page),
          limit: String(limit),
        });

        if (active) {
          setRecordsState({ loading: false, error: null, data: result });
        }
      } catch (error) {
        if (active) {
          setRecordsState({
            loading: false,
            error: getErrorMessage(error),
            data: null,
          });
        }
      }
    }

    void loadRecords();

    return () => {
      active = false;
    };
  }, [limit, page, query, refreshKey, stage, status]);

  async function handleCreateCandidate(values: ReturnType<typeof getDefaultCandidateValues>) {
    await createRecord(values);

    setCreateFormVersion((currentValue) => currentValue + 1);
    setRefreshKey((currentValue) => currentValue + 1);
  }

  function handlePageChange(nextPage: number) {
    const params = new URLSearchParams(searchParams.toString());

    if (nextPage <= 1) {
      params.delete("page");
    } else {
      params.set("page", String(nextPage));
    }

    const nextQuery = params.toString();
    router.replace(nextQuery ? `?${nextQuery}` : "/");
  }

  function handlePageSelect(nextPage: string) {
    handlePageChange(sanitizePositiveInteger(nextPage, 1));
  }

  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">{branding.companyName}</p>
          <h1>{branding.appName}</h1>
          {branding.appTagline ? <p>{branding.appTagline}</p> : null}
        </section>

        <CandidateFilters />

        <div className="section-grid columns">
          <section className="section-card">
            <header>
              <h2>{branding.candidatePlural}</h2>
              <p>
                This list is loaded from <strong>GET /records</strong> and keeps query-parameter
                filtering in sync with the URL.
              </p>
              <p>
                Showing <strong>{records.length}</strong> of <strong>{total}</strong>{" "}
                {branding.candidatePlural.toLowerCase()} on page <strong>{currentPage}</strong> of{" "}
                <strong>{totalPages}</strong>.
              </p>
            </header>

            {hasActiveFilters ? (
              <div className="feedback warning" role="status" aria-live="polite">
                Active filters are limiting the list{status ? `, including status "${status}"` : ""}
                {stage ? `${status ? " and" : ", including"} stage "${stage}"` : ""}
                {query ? `${status || stage ? ", plus" : ", including"} search "${query}"` : ""}.
              </div>
            ) : null}

            <AsyncState
              loading={recordsState.loading}
              error={recordsState.error}
              loadingText="Loading candidates..."
              isEmpty={records.length === 0}
              emptyState={
                <div className="empty-state">
                  No {branding.candidatePlural.toLowerCase()} are available for the current view.
                </div>
              }
            >
              <CandidateTable records={records} />
              <div className="pagination-bar">
                <button
                  className="button ghost"
                  type="button"
                  disabled={currentPage <= 1 || recordsState.loading}
                  onClick={() => handlePageChange(currentPage - 1)}
                >
                  Previous page
                </button>
                <p className="pagination-copy">
                  Page {currentPage} of {totalPages} · {total} total results
                </p>
                <div className="pagination-select">
                  <label htmlFor="page-select">Jump to page</label>
                  <div className="select-wrap">
                    <select
                      id="page-select"
                      name="page-select"
                      value={String(currentPage)}
                      onChange={(event) => handlePageSelect(event.target.value)}
                    >
                      {Array.from({ length: totalPages }, (_, index) => {
                        const pageNumber = index + 1;

                        return (
                          <option key={pageNumber} value={pageNumber}>
                            Page {pageNumber}
                          </option>
                        );
                      })}
                    </select>
                  </div>
                </div>
                <button
                  className="button ghost"
                  type="button"
                  disabled={currentPage >= totalPages || recordsState.loading}
                  onClick={() => handlePageChange(currentPage + 1)}
                >
                  Next page
                </button>
              </div>
            </AsyncState>
          </section>

          <div className="sticky-column">
            <CandidateForm
              key={createFormVersion}
              heading="Register new candidate"
              description="Submit a new candidate to the pipeline using the POST record endpoint."
              submitLabel="Create candidate"
              initialValues={getDefaultCandidateValues()}
              onSubmit={handleCreateCandidate}
            />
          </div>
        </div>
      </div>
    </main>
  );
}

function sanitizePositiveInteger(value: string | null, fallback: number) {
  const parsedValue = Number(value);

  if (!Number.isFinite(parsedValue) || parsedValue < 1) {
    return fallback;
  }

  return Math.floor(parsedValue);
}