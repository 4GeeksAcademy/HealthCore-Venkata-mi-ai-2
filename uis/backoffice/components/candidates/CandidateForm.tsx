"use client";

import { ChangeEvent, FormEvent, useState } from "react";
import {
  CandidateFormValues,
  candidateStageOptions,
  candidateStatusOptions,
} from "@/types/candidate";
import { FieldErrors, validateCandidateInput } from "@/lib/validators";
import { getErrorMessage } from "@/lib/api-client";
import { ErrorActions } from "@/components/async/ErrorActions";

interface CandidateFormProps {
  heading: string;
  description: string;
  submitLabel: string;
  initialValues: CandidateFormValues;
  onSubmit: (values: CandidateFormValues) => Promise<void>;
}

type SubmissionState = {
  status: "idle" | "submitting" | "success" | "error";
  message: string | null;
};

export function CandidateForm({
  heading,
  description,
  submitLabel,
  initialValues,
  onSubmit,
}: CandidateFormProps) {
  const [values, setValues] = useState(() => initialValues);
  const [errors, setErrors] = useState<FieldErrors<keyof CandidateFormValues>>({});
  const [submission, setSubmission] = useState<SubmissionState>({
    status: "idle",
    message: null,
  });

  function handleChange(
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) {
    const { name, value } = event.target;

    setValues((currentValues) => ({
      ...currentValues,
      [name]: value,
    }));

    setErrors((currentErrors) => ({
      ...currentErrors,
      [name]: undefined,
    }));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const nextErrors = validateCandidateInput(values);

    if (Object.keys(nextErrors).length > 0) {
      setErrors(nextErrors);
      setSubmission({
        status: "error",
        message: "Resolve the validation errors before submitting.",
      });
      return;
    }

    setSubmission({ status: "submitting", message: null });
    let outcome: SubmissionState = {
      status: "error",
      message: "Unable to save candidate data.",
    };
    try {
      await onSubmit(values);
      outcome = {
        status: "success",
        message: "Changes saved successfully.",
      };
    } catch (error) {
      outcome = {
        status: "error",
        message: getErrorMessage(error),
      };
    } finally {
      setSubmission(outcome);
    }
  }

  return (
    <section className="section-card form-card">
      <header>
        <h2>{heading}</h2>
        <p>{description}</p>
      </header>

      {submission.status === "submitting" ? (
        <div className="feedback info" role="status" aria-live="polite">
          Saving changes...
        </div>
      ) : null}

      {submission.status === "success" && submission.message ? (
        <div className="feedback info" role="status" aria-live="polite">
          {submission.message}
        </div>
      ) : null}

      {submission.status === "error" && submission.message ? (
        <div className="feedback error" role="alert">
          <p>{submission.message}</p>
          <ErrorActions
            homeHref="/hiring"
            onRetry={() => setSubmission({ status: "idle", message: null })}
          />
        </div>
      ) : null}

      <form className="stack" onSubmit={handleSubmit}>
        <div className="field-grid">
          <FormField label="Full name" name="fullName" value={values.fullName} onChange={handleChange} error={errors.fullName} />
          <FormField label="Email" name="email" type="email" value={values.email} onChange={handleChange} error={errors.email} />
          <FormField label="Phone" name="phone" value={values.phone} onChange={handleChange} error={errors.phone} />
          <FormField label="Position applied for" name="position" value={values.position} onChange={handleChange} error={errors.position} />
          <FormField label="LinkedIn URL" name="linkedinUrl" value={values.linkedinUrl} onChange={handleChange} error={errors.linkedinUrl} />
          <FormField label="CV link" name="cvUrl" value={values.cvUrl} onChange={handleChange} error={errors.cvUrl} />
          <FormField label="Application date" name="applicationDate" type="date" value={values.applicationDate} onChange={handleChange} error={errors.applicationDate} />
          <SelectField label="Status" name="status" value={values.status} onChange={handleChange} error={errors.status} options={candidateStatusOptions} />
          <SelectField label="Stage" name="stage" value={values.stage} onChange={handleChange} error={errors.stage} options={candidateStageOptions} />
        </div>

        <div className="field">
          <label htmlFor="experience">Experience</label>
          <textarea
            id="experience"
            name="experience"
            value={values.experience}
            onChange={handleChange}
            placeholder="Summarize relevant experience"
          />
          {errors.experience ? <span className="field-error">{errors.experience}</span> : null}
        </div>

        <div className="button-row">
          <button className="button" type="submit" disabled={submission.status === "submitting"}>
            {submitLabel}
          </button>
        </div>
      </form>
    </section>
  );
}

interface BaseFieldProps {
  label: string;
  name: keyof CandidateFormValues;
  value: string;
  error?: string;
  onChange: (
    event: ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>,
  ) => void;
}

function FormField({
  label,
  name,
  value,
  error,
  onChange,
  type = "text",
}: BaseFieldProps & { type?: string }) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <input id={name} name={name} type={type} value={value} onChange={onChange} />
      {error ? <span className="field-error">{error}</span> : null}
    </div>
  );
}

function SelectField({
  label,
  name,
  value,
  error,
  onChange,
  options,
}: BaseFieldProps & { options: readonly string[] }) {
  return (
    <div className="field">
      <label htmlFor={name}>{label}</label>
      <div className="select-wrap">
        <select id={name} name={name} value={value} onChange={onChange}>
          {options.map((option) => (
            <option key={option} value={option}>
              {option}
            </option>
          ))}
        </select>
      </div>
      {error ? <span className="field-error">{error}</span> : null}
    </div>
  );
}