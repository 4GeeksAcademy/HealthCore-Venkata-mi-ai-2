"use client";

import Link from "next/link";
import { useCallback, useEffect, useState, type FormEvent } from "react";
import { ErrorActions } from "@/components/async/ErrorActions";
import { ApiError, authedFetch } from "@/lib/authed-fetch";

type Section = {
  department_id?: string;
  owner_name?: string;
  owner_role?: string;
  key_aspects?: string[];
  open_questions?: string[];
};

type TicketSummary = {
  ticket_id: string;
  rfp_id?: string | null;
  status: string;
  original_filename?: string;
  phi_detected?: boolean;
  client_name?: string;
  discard_message?: string;
  pipeline_message?: string;
  created_at?: string;
};

type TicketDetail = TicketSummary & {
  metadata?: {
    client_name?: string;
    client_country?: string;
    program_type?: string;
    covered_population?: number | null;
    deadline?: string;
    budget_range?: string;
    currency?: string;
    cost_band?: string;
    estimated_tokens?: number;
    flesch_reading_ease?: number | null;
    flesch_kincaid_grade?: number | null;
    gunning_fog?: number | null;
    readability_note?: string;
    open_questions?: string[];
  } | null;
  sections?: Section[];
  sales_summary?: string;
  part2_guard?: string;
  conflicts?: { field?: string; resolution?: string }[];
};

const STATUS_LABEL: Record<string, string> = {
  analyzing: "Analyzing",
  intake_complete: "Intake complete",
  discarded: "Discarded",
  failed: "Failed",
};

function statusClass(status: string): string {
  return `rfp-status rfp-status-${status}`;
}

export default function RfpIntakePage() {
  const [tickets, setTickets] = useState<TicketSummary[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<TicketDetail | null>(null);
  const [pageLoading, setPageLoading] = useState(true);
  const [pageError, setPageError] = useState<string | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [detailError, setDetailError] = useState<string | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);

  const loadTickets = useCallback(async () => {
    const response = await authedFetch("/rfp/tickets");
    const body = (await response.json()) as { tickets?: TicketSummary[] };
    setTickets(Array.isArray(body?.tickets) ? body.tickets : []);
  }, []);

  const loadDetail = useCallback(async (ticketId: string, quiet = false) => {
    if (!quiet) {
      setDetailLoading(true);
      setDetailError(null);
    }
    try {
      const response = await authedFetch(`/rfp/tickets/${ticketId}`);
      const body = (await response.json()) as TicketDetail;
      setDetail(body);
    } catch {
      if (!quiet) {
        setDetail(null);
        setDetailError("We couldn't load that ticket. Retry, or go back to the list.");
      }
    } finally {
      if (!quiet) {
        setDetailLoading(false);
      }
    }
  }, []);

  const refresh = useCallback(async () => {
    setPageLoading(true);
    setPageError(null);
    try {
      await loadTickets();
    } catch (caught) {
      setPageError(
        caught instanceof ApiError && caught.status === 503
          ? "RFP intake storage is not available. Please try again later."
          : "We couldn't load RFP tickets. Please try again.",
      );
    } finally {
      setPageLoading(false);
    }
  }, [loadTickets]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await loadTickets();
        if (!cancelled) {
          setPageError(null);
        }
      } catch (caught) {
        if (!cancelled) {
          setPageError(
            caught instanceof ApiError && caught.status === 503
              ? "RFP intake storage is not available. Please try again later."
              : "We couldn't load RFP tickets. Please try again.",
          );
        }
      } finally {
        if (!cancelled) {
          setPageLoading(false);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadTickets]);

  useEffect(() => {
    if (!tickets.some((ticket) => ticket.status === "analyzing")) {
      return;
    }
    const timer = window.setInterval(() => {
      void loadTickets().catch(() => {
        setUploadError("We couldn't refresh ticket status. The page will try again.");
      });
      if (selectedId) {
        void loadDetail(selectedId, true);
      }
    }, 3000);
    return () => window.clearInterval(timer);
  }, [tickets, selectedId, loadTickets, loadDetail]);

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const input = form.elements.namedItem("rfp");
    const file = input instanceof HTMLInputElement ? input.files?.[0] : undefined;
    if (!file || uploading) return;
    setUploading(true);
    setUploadError(null);
    try {
      const body = new FormData();
      body.append("file", file);
      const response = await authedFetch("/rfp/tickets", { method: "POST", body });
      const accepted = (await response.json()) as { ticket_id?: string };
      form.reset();
      await loadTickets();
      if (accepted?.ticket_id) {
        setSelectedId(accepted.ticket_id);
        await loadDetail(accepted.ticket_id);
      }
    } catch (caught) {
      setUploadError(
        caught instanceof ApiError && caught.message
          ? caught.message
          : "That PDF could not be uploaded. Please try again.",
      );
    } finally {
      setUploading(false);
    }
  }

  async function onReprocess(ticketId: string) {
    setDetailError(null);
    try {
      await authedFetch(`/rfp/tickets/${ticketId}/reprocess`, { method: "POST" });
      await loadTickets();
      await loadDetail(ticketId);
    } catch {
      setDetailError("This ticket could not be queued again. Retry, or contact HealthCore Digital support.");
    }
  }

  const metadata = detail?.metadata;

  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Revenue Cycle</p>
          <h1>RFP intake</h1>
          <p>
            Upload an institutional PDF. Revenue Cycle can see who to ask in
            Clinical Operations and Compliance without opening the file.
          </p>
          <p>Do not upload documents that name a patient or include a diagnosis.</p>
          <div className="inline-actions">
            <Link className="link-button secondary" href="/" prefetch={false}>
              Back to welcome
            </Link>
          </div>
        </section>

        {pageLoading ? (
          <section className="section-card" aria-busy="true">
            <p className="muted-text" role="status">
              Loading tickets…
            </p>
          </section>
        ) : null}

        {pageError ? (
          <section className="section-card" role="alert">
            <h2>Tickets are unavailable</h2>
            <p>{pageError}</p>
            <ErrorActions onRetry={() => void refresh()} />
          </section>
        ) : null}

        {!pageLoading && !pageError ? (
          <>
            <section className="section-card">
              <h2>Upload a PDF</h2>
              <form className="field" onSubmit={onUpload}>
                <label htmlFor="rfp">Request for proposal (PDF only)</label>
                <input id="rfp" name="rfp" type="file" accept="application/pdf,.pdf" required />
                <div className="inline-actions">
                  <button className="button" type="submit" disabled={uploading}>
                    {uploading ? "Uploading…" : "Create ticket"}
                  </button>
                </div>
              </form>
              {uploadError ? (
                <div role="alert">
                  <p className="field-error">{uploadError}</p>
                  <ErrorActions onRetry={() => setUploadError(null)} retryLabel="Dismiss" />
                </div>
              ) : null}
            </section>

            <section className="section-card">
              <h2>Tickets</h2>
              {tickets.length === 0 ? (
                <p className="muted-text">No RFPs have been uploaded yet.</p>
              ) : (
                <div className="rfp-list">
                  {tickets.map((ticket) => (
                    <button
                      key={ticket.ticket_id}
                      type="button"
                      className="button secondary"
                      onClick={() => {
                        setSelectedId(ticket.ticket_id);
                        void loadDetail(ticket.ticket_id);
                      }}
                    >
                      <span className={statusClass(ticket.status)}>
                        {STATUS_LABEL[ticket.status] ?? ticket.status}
                      </span>{" "}
                      {ticket.client_name || ticket.original_filename || ticket.ticket_id}
                    </button>
                  ))}
                </div>
              )}
            </section>

            {selectedId ? (
              <section className="section-card" aria-busy={detailLoading}>
                {detailLoading ? (
                  <p className="muted-text" role="status">
                    Loading ticket…
                  </p>
                ) : null}
                {detailError ? (
                  <div role="alert">
                    <p>{detailError}</p>
                    <ErrorActions onRetry={() => void loadDetail(selectedId)} />
                  </div>
                ) : null}
                {detail && !detailError ? (
                  <>
                    <header>
                      <h2>{detail.client_name || detail.original_filename || "Ticket"}</h2>
                      <p>
                        <span className={statusClass(detail.status)}>
                          {STATUS_LABEL[detail.status] ?? detail.status}
                        </span>
                        {detail.rfp_id ? ` · ${detail.rfp_id}` : ""}
                      </p>
                    </header>
                    {detail.phi_detected ? (
                      <p className="rfp-banner">
                        Patient information was detected and removed. Claire Whitfield
                        (Compliance) must review before any proposal draft.
                      </p>
                    ) : null}
                    {detail.status === "discarded" ? (
                      <p>{detail.discard_message || "This document was discarded."}</p>
                    ) : null}
                    {detail.status === "failed" ? (
                      <p>{detail.pipeline_message || "Analysis did not finish."}</p>
                    ) : null}
                    {detail.status === "analyzing" ? (
                      <p className="muted-text" role="status">
                        Analysis is still running. This page refreshes every few seconds.
                      </p>
                    ) : null}
                    {detail.sales_summary ? <p>{detail.sales_summary}</p> : null}
                    {metadata ? (
                      <p>
                        {metadata.client_country ? `Country ${metadata.client_country}. ` : ""}
                        {metadata.program_type ? `Program ${metadata.program_type}. ` : ""}
                        {metadata.covered_population != null
                          ? `Covered population ${metadata.covered_population}. `
                          : ""}
                        {metadata.currency ? `Currency ${metadata.currency}. ` : ""}
                        {metadata.deadline ? `Deadline ${metadata.deadline}. ` : ""}
                        {metadata.cost_band ? `Processing cost ${metadata.cost_band}.` : ""}
                      </p>
                    ) : null}
                    {metadata?.readability_note ? <p>{metadata.readability_note}</p> : null}
                    {(detail.sections ?? []).map((section) => (
                      <article key={section.department_id}>
                        <h3>
                          Ask {section.owner_name || "the department owner"} (
                          {section.department_id})
                        </h3>
                        <p className="muted-text">{section.owner_role}</p>
                        <ul>
                          {(section.key_aspects ?? []).length === 0 ? (
                            <li>No department-specific passage was found.</li>
                          ) : (
                            (section.key_aspects ?? []).map((aspect) => <li key={aspect}>{aspect}</li>)
                          )}
                        </ul>
                        {(section.open_questions ?? []).length > 0 ? (
                          <p>Open: {(section.open_questions ?? []).join(" ")}</p>
                        ) : null}
                      </article>
                    ))}
                    {(metadata?.open_questions ?? []).length > 0 ? (
                      <p>Ticket questions: {(metadata?.open_questions ?? []).join(" ")}</p>
                    ) : null}
                    {(detail.conflicts ?? []).length > 0 ? (
                      <p>
                        Departments disagreed on{" "}
                        {(detail.conflicts ?? []).map((conflict) => conflict.field).filter(Boolean).join(", ")}.
                        That stays unresolved for the later approval step.
                      </p>
                    ) : null}
                    {detail.status === "failed" || detail.status === "discarded" ? (
                      <div className="inline-actions">
                        <button
                          type="button"
                          className="button"
                          onClick={() => void onReprocess(detail.ticket_id)}
                        >
                          Run again
                        </button>
                      </div>
                    ) : null}
                  </>
                ) : null}
              </section>
            ) : null}
          </>
        ) : null}
      </div>
    </main>
  );
}
