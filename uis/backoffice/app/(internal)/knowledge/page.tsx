"use client";

import Link from "next/link";
import { useState, type FormEvent } from "react";
import { ErrorActions } from "@/components/async/ErrorActions";
import { ApiError, authedFetch } from "@/lib/authed-fetch";

type KnowledgeAnswer = {
  answer: string;
};

const EXAMPLE_QUESTIONS = [
  "Is there a charge for cancelling 12 hours in advance?",
  "What do I need to bring to my first appointment?",
  "Do you accept Medicaid in Georgia?",
  "How long does an internal referral take?",
];

const MAX_QUESTION_LENGTH = 1000;

export default function KnowledgeAssistantPage() {
  const [question, setQuestion] = useState("");
  const [askedQuestion, setAskedQuestion] = useState<string | null>(null);
  const [answer, setAnswer] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(text: string) {
    const trimmed = text.trim();
    if (!trimmed || loading) return;
    setLoading(true);
    setError(null);
    setAnswer(null);
    setAskedQuestion(trimmed);
    try {
      const response = await authedFetch("/knowledge/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: trimmed }),
      });
      const body = (await response.json()) as KnowledgeAnswer;
      if (typeof body?.answer !== "string" || !body.answer.trim()) {
        throw new Error("empty");
      }
      setAnswer(body.answer);
    } catch (caught) {
      setError(
        caught instanceof ApiError && caught.status === 503
          ? "The knowledge assistant is temporarily unavailable. Please try again in a moment."
          : "We couldn't get an answer for that question. Please try again.",
      );
    } finally {
      setLoading(false);
    }
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void ask(question);
  }

  return (
    <main className="app-shell knowledge-page">
      <div className="page-frame">
        <section className="page-header">
          <p className="eyebrow">HealthCore Digital · Patient Experience</p>
          <h1>Coordinator Knowledge Assistant</h1>
          <p>
            Ask about accepted insurance, appointments and cancellations,
            internal referrals, or the new patient checklist. Answers come only
            from HealthCore policy documents.
          </p>
          <p>
            Do not type patient names, record numbers, member IDs, or
            diagnoses.
          </p>
          <div className="inline-actions">
            <Link className="link-button secondary" href="/" prefetch={false}>
              Back to welcome
            </Link>
          </div>
        </section>

        <section className="section-card">
          <form className="stack" onSubmit={onSubmit}>
            <div className="field">
              <label htmlFor="knowledge-question">Question</label>
              <textarea
                id="knowledge-question"
                value={question}
                maxLength={MAX_QUESTION_LENGTH}
                placeholder="e.g. Is there a charge for cancelling 12 hours in advance?"
                onChange={(event) => setQuestion(event.target.value)}
              />
            </div>
            <div className="button-row">
              <button
                type="submit"
                className="button"
                disabled={loading || !question.trim()}
              >
                {loading ? "Finding the answer…" : "Ask"}
              </button>
            </div>
          </form>
          <div className="knowledge-examples">
            <p className="muted-text">Common desk questions:</p>
            <div className="inline-actions">
              {EXAMPLE_QUESTIONS.map((example) => (
                <button
                  key={example}
                  type="button"
                  className="button ghost"
                  disabled={loading}
                  onClick={() => {
                    setQuestion(example);
                    void ask(example);
                  }}
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        </section>

        {loading ? (
          <section className="section-card">
            <p className="muted-text" role="status">
              Searching HealthCore policies and drafting an answer…
            </p>
          </section>
        ) : null}

        {error ? (
          <section className="section-card" role="alert">
            <p>{error}</p>
            <ErrorActions
              onRetry={askedQuestion ? () => void ask(askedQuestion) : undefined}
            />
          </section>
        ) : null}

        {!loading && !error && answer ? (
          <section className="section-card" aria-live="polite">
            <h2>Answer</h2>
            <p className="muted-text">Question: {askedQuestion}</p>
            <div className="knowledge-answer">{answer}</div>
          </section>
        ) : null}
      </div>
    </main>
  );
}
