"use client";

import { FormEvent, useState } from "react";
import { patchRecord } from "@/lib/records-service";
import {
  CandidateRecord,
  candidateStageOptions,
  candidateStatusOptions,
} from "@/types/candidate";

interface CandidateStatusStagePanelProps {
  candidate: CandidateRecord;
  onUpdated: (candidate: CandidateRecord) => void;
}

export function CandidateStatusStagePanel({
  candidate,
  onUpdated,
}: CandidateStatusStagePanelProps) {
  const [status, setStatus] = useState(() => candidate.status);
  const [stage, setStage] = useState(() => candidate.stage);
  const [submissionState, setSubmissionState] = useState<{
    status: "idle" | "submitting" | "success" | "error";
    message: string | null;
  }>({ status: "idle", message: null });

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    try {
      setSubmissionState({ status: "submitting", message: null });
      const updatedCandidate = await patchRecord(candidate.id, { status, stage });
      onUpdated(updatedCandidate);
      setSubmissionState({
        status: "success",
        message: "Status and stage updated.",
      });
    } catch (error) {
      setSubmissionState({
        status: "error",
        message:
          error instanceof Error ? error.message : "Unable to update status and stage.",
      });
    }
  }

  return (
    <section className="section-card compact-card">
      <header>
        <h2>Update current progress</h2>
        <p>Patch the current status and stage without leaving the detail page.</p>
      </header>

      {submissionState.status === "submitting" ? (
        <div className="feedback info" role="status" aria-live="polite">
          Saving progress update...
        </div>
      ) : null}

      {submissionState.status === "success" && submissionState.message ? (
        <div className="feedback info" role="status" aria-live="polite">
          {submissionState.message}
        </div>
      ) : null}

      {submissionState.status === "error" && submissionState.message ? (
        <div className="feedback error" role="alert">
          {submissionState.message}
        </div>
      ) : null}

      <form className="stack" onSubmit={handleSubmit}>
        <div className="controls-grid">
          <div className="field">
            <label htmlFor="candidate-status">Status</label>
            <div className="select-wrap">
              <select
                id="candidate-status"
                value={status}
                onChange={(event) => setStatus(event.target.value as CandidateRecord["status"])}
              >
                {candidateStatusOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="field">
            <label htmlFor="candidate-stage">Stage</label>
            <div className="select-wrap">
              <select
                id="candidate-stage"
                value={stage}
                onChange={(event) => setStage(event.target.value as CandidateRecord["stage"])}
              >
                {candidateStageOptions.map((option) => (
                  <option key={option} value={option}>
                    {option}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        <div className="button-row">
          <button className="button" type="submit" disabled={submissionState.status === "submitting"}>
            Save status and stage
          </button>
        </div>
      </form>
    </section>
  );
}