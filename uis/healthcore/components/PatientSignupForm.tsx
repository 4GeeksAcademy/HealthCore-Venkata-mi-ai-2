"use client";

import { FormEvent, useState } from "react";
import { validatePatientSignup } from "@/lib/signup-validation";
import type {
  PatientSignupFormErrors,
  PatientSignupFormValues,
} from "@/types/content";

const emptyValues: PatientSignupFormValues = {
  fullName: "",
  email: "",
  phone: "",
  concerns: "",
};

export function PatientSignupForm() {
  const [values, setValues] = useState<PatientSignupFormValues>(emptyValues);
  const [errors, setErrors] = useState<PatientSignupFormErrors>({});
  const [submitted, setSubmitted] = useState(false);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const nextErrors = validatePatientSignup(values);
    setErrors(nextErrors);

    if (Object.keys(nextErrors).length === 0) {
      setSubmitted(true);
      setValues(emptyValues);
    } else {
      setSubmitted(false);
    }
  }

  return (
    <div className="surface-card">
      <h2>Patient sign-up</h2>
      <p className="section-lead">
        Complete the form and a HealthCore specialist will contact you with next
        steps. No patient data is stored in this demo UI.
      </p>

      {submitted ? (
        <div className="success-banner" role="status">
          Your request was submitted successfully. A HealthCore specialist will
          reach out soon.
        </div>
      ) : null}

      <form className="form-stack" onSubmit={handleSubmit} noValidate>
        <label htmlFor="fullName">
          Full name
          <input
            id="fullName"
            name="fullName"
            autoComplete="name"
            value={values.fullName}
            onChange={(event) =>
              setValues((current) => ({ ...current, fullName: event.target.value }))
            }
          />
          {errors.fullName ? <span className="field-error">{errors.fullName}</span> : null}
        </label>

        <label htmlFor="email">
          Email address
          <input
            id="email"
            name="email"
            type="email"
            autoComplete="email"
            value={values.email}
            onChange={(event) =>
              setValues((current) => ({ ...current, email: event.target.value }))
            }
          />
          {errors.email ? <span className="field-error">{errors.email}</span> : null}
        </label>

        <label htmlFor="phone">
          Phone number
          <input
            id="phone"
            name="phone"
            type="tel"
            autoComplete="tel"
            value={values.phone}
            onChange={(event) =>
              setValues((current) => ({ ...current, phone: event.target.value }))
            }
          />
          {errors.phone ? <span className="field-error">{errors.phone}</span> : null}
        </label>

        <label htmlFor="concerns">
          Primary health concerns
          <textarea
            id="concerns"
            name="concerns"
            rows={5}
            value={values.concerns}
            onChange={(event) =>
              setValues((current) => ({ ...current, concerns: event.target.value }))
            }
          />
          {errors.concerns ? (
            <span className="field-error">{errors.concerns}</span>
          ) : null}
        </label>

        <button className="btn btn-primary" type="submit">
          Save my spot
        </button>
      </form>
    </div>
  );
}
