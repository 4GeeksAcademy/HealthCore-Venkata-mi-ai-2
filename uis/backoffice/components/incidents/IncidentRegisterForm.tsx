"use client";

import { FormEvent, useState } from "react";
import { createIncident, type FieldApiError } from "@/lib/incidents-api";
import {
  INCIDENT_BRANCHES,
  INCIDENT_CATEGORIES,
  INCIDENT_ORIGINS,
  type IncidentBranch,
  type IncidentCategory,
  type IncidentOrigin,
  type IncidentStatus,
} from "@/lib/incidents-constants";
import { getUserFacingError } from "@/lib/user-facing-error";

type FieldErrors = Partial<
  Record<"title" | "description" | "category" | "origin" | "branch" | "status", string>
>;

const INITIAL = {
  title: "",
  description: "",
  category: "patient_experience" as IncidentCategory,
  status: "open" as IncidentStatus,
  origin: "customer" as IncidentOrigin,
  branch: "central" as IncidentBranch,
};

export function IncidentRegisterForm() {
  const [form, setForm] = useState(INITIAL);
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const branchHighlighted = form.origin === "branch";

  function validateClient(): FieldErrors {
    const errors: FieldErrors = {};
    if (!form.title.trim()) errors.title = "Title is required.";
    if (!form.description.trim()) errors.description = "Description is required.";
    if (!form.category) errors.category = "Category is required.";
    if (!form.origin) errors.origin = "Origin is required.";
    if (!form.branch) errors.branch = "Branch is required.";
    return errors;
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setSuccess(null);
    setFormError(null);
    const clientErrors = validateClient();
    setFieldErrors(clientErrors);
    if (Object.keys(clientErrors).length > 0) return;

    setSubmitting(true);
    try {
      const created = await createIncident({
        title: form.title.trim(),
        description: form.description.trim(),
        category: form.category,
        status: form.status === "in_progress" ? "in_progress" : "open",
        origin: form.origin,
        branch: form.branch,
      });
      setForm(INITIAL);
      setFieldErrors({});
      setSuccess(`Incident registered (id ${created.id}).`);
    } catch (error) {
      const field = (error as FieldApiError).field;
      const message = getUserFacingError(
        error,
        "We could not register this incident. Please try again.",
      );
      if (field) {
        setFieldErrors({ [field]: message });
      } else {
        setFormError(message);
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form className="section-card" onSubmit={onSubmit} noValidate>
      <h2>Register incident</h2>
      <p className="muted-text">
        Log a new operational incident for HealthCore Digital staff. Required
        fields must be completed before submit.
      </p>

      {success ? (
        <p role="status" className="notice-success">
          {success}
        </p>
      ) : null}
      {formError ? (
        <p role="alert" className="notice-error">
          {formError}
        </p>
      ) : null}

      <label>
        Title
        <input
          value={form.title}
          onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          disabled={submitting}
          required
          maxLength={200}
        />
        {fieldErrors.title ? (
          <span className="field-error" role="alert">
            {fieldErrors.title}
          </span>
        ) : null}
      </label>

      <div
        className="notice-warning"
        role="note"
        style={{
          margin: "1rem 0",
          padding: "0.85rem 1rem",
          border: "2px solid #b45309",
          background: "#fff7ed",
          color: "#7c2d12",
          fontWeight: 600,
        }}
      >
        Do not enter identifying patient data (name, date of birth, medical
        record number, phone, email, or address). Reference patients only with
        opaque internal identifiers if needed.
      </div>

      <label>
        Description
        <textarea
          value={form.description}
          onChange={(e) =>
            setForm((f) => ({ ...f, description: e.target.value }))
          }
          disabled={submitting}
          required
          rows={5}
          maxLength={8000}
        />
        {fieldErrors.description ? (
          <span className="field-error" role="alert">
            {fieldErrors.description}
          </span>
        ) : null}
      </label>

      <label>
        Category
        <select
          value={form.category}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              category: e.target.value as IncidentCategory,
            }))
          }
          disabled={submitting}
          required
        >
          {INCIDENT_CATEGORIES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {fieldErrors.category ? (
          <span className="field-error" role="alert">
            {fieldErrors.category}
          </span>
        ) : null}
      </label>

      <label>
        Origin
        <select
          value={form.origin}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              origin: e.target.value as IncidentOrigin,
            }))
          }
          disabled={submitting}
          required
        >
          {INCIDENT_ORIGINS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {fieldErrors.origin ? (
          <span className="field-error" role="alert">
            {fieldErrors.origin}
          </span>
        ) : null}
      </label>

      <label
        style={
          branchHighlighted
            ? {
                outline: "2px solid #0369a1",
                outlineOffset: "4px",
                background: "#e0f2fe",
                padding: "0.75rem",
                borderRadius: "0.35rem",
              }
            : undefined
        }
      >
        Branch
        {branchHighlighted ? (
          <span className="muted-text"> — reporting from a specific clinic</span>
        ) : null}
        <select
          value={form.branch}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              branch: e.target.value as IncidentBranch,
            }))
          }
          disabled={submitting}
          required
        >
          {INCIDENT_BRANCHES.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        {fieldErrors.branch ? (
          <span className="field-error" role="alert">
            {fieldErrors.branch}
          </span>
        ) : null}
      </label>

      <label>
        Initial status
        <select
          value={form.status}
          onChange={(e) =>
            setForm((f) => ({
              ...f,
              status: e.target.value as IncidentStatus,
            }))
          }
          disabled={submitting}
        >
          <option value="open">Open</option>
          <option value="in_progress">In progress</option>
        </select>
        {fieldErrors.status ? (
          <span className="field-error" role="alert">
            {fieldErrors.status}
          </span>
        ) : null}
      </label>

      <div className="inline-actions" style={{ marginTop: "1rem" }}>
        <button type="submit" className="link-button" disabled={submitting}>
          {submitting ? "Saving…" : "Register incident"}
        </button>
      </div>
    </form>
  );
}
