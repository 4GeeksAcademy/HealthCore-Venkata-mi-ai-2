"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { AsyncState } from "@/components/async/AsyncState";
import { CandidateDetailCard } from "@/components/candidates/CandidateDetailCard";
import { CandidateEditForm } from "@/components/candidates/CandidateEditForm";
import { CandidateNotesSection } from "@/components/candidates/CandidateNotesSection";
import { CandidateStatusStagePanel } from "@/components/candidates/CandidateStatusStagePanel";
import { getErrorMessage } from "@/lib/api-client";
import { getRecordById } from "@/lib/records-service";
import { AsyncDataState } from "@/types/api";
import { CandidateRecord } from "@/types/candidate";

export function CandidateDetailPage() {
  const params = useParams<{ id: string }>();
  const recordId = typeof params.id === "string" ? params.id : "";
  const [reloadKey, setReloadKey] = useState(0);
  const [candidateState, setCandidateState] = useState<AsyncDataState<CandidateRecord>>({
    loading: true,
    error: null,
    data: null,
  });

  useEffect(() => {
    if (!recordId) {
      return;
    }

    let active = true;

    async function loadCandidate() {
      setCandidateState({ loading: true, error: null, data: null });
      try {
        const candidate = await getRecordById(recordId);

        if (active) {
          setCandidateState({ loading: false, error: null, data: candidate });
        }
      } catch (error) {
        if (active) {
          setCandidateState({
            loading: false,
            error: getErrorMessage(error),
            data: null,
          });
        }
      } finally {
        if (active) {
          setCandidateState((current) =>
            current.loading ? { ...current, loading: false } : current,
          );
        }
      }
    }

    void loadCandidate();

    return () => {
      active = false;
    };
  }, [recordId, reloadKey]);

  return (
    <main className="app-shell">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">Candidate detail</p>
          <h1>Candidate profile</h1>
          <p>Review and update one candidate record without leaving the App Router flow.</p>
          <div className="inline-actions">
            <Link className="link-button secondary" href="/hiring">
              Back to candidate list
            </Link>
          </div>
        </section>

        {!recordId ? (
          <div className="feedback error" role="alert">
            Candidate id is missing from the route.
          </div>
        ) : null}

        <AsyncState
          loading={candidateState.loading}
          error={candidateState.error}
          loadingText="Loading candidate detail..."
          onRetry={() => setReloadKey((key) => key + 1)}
          homeHref="/hiring"
        >
          {candidateState.data ? (
            <div className="section-grid">
              <CandidateDetailCard candidate={candidateState.data} />
              <div className="section-grid detail-columns">
                <div className="stack">
                  <CandidateStatusStagePanel
                    key={`${candidateState.data.id}:${candidateState.data.status}:${candidateState.data.stage}`}
                    candidate={candidateState.data}
                    onUpdated={(candidate) =>
                      setCandidateState({ loading: false, error: null, data: candidate })
                    }
                  />
                  <CandidateEditForm
                    candidate={candidateState.data}
                    onUpdated={(candidate) =>
                      setCandidateState({ loading: false, error: null, data: candidate })
                    }
                  />
                </div>

                <div className="sticky-column">
                  <CandidateNotesSection recordId={candidateState.data.id} />
                </div>
              </div>
            </div>
          ) : (
            <div className="empty-state">No candidate data is available for this route.</div>
          )}
        </AsyncState>
      </div>
    </main>
  );
}