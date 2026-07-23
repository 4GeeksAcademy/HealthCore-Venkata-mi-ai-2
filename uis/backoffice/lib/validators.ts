import {
  CandidateFormValues,
  candidateStageOptions,
  candidateStatusOptions,
} from "@/types/candidate";

export type FieldErrors<T extends string> = Partial<Record<T, string>>;

export function validateCandidateInput(
  values: CandidateFormValues,
): FieldErrors<keyof CandidateFormValues> {
  const errors: FieldErrors<keyof CandidateFormValues> = {};

  if (!values.fullName.trim()) {
    errors.fullName = "Full name is required.";
  }

  if (!values.email.trim()) {
    errors.email = "Email is required.";
  } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
    errors.email = "Enter a valid email address.";
  }

  if (!values.position.trim()) {
    errors.position = "Position is required.";
  }

  if (!values.applicationDate) {
    errors.applicationDate = "Application date is required.";
  }

  if (!candidateStatusOptions.includes(values.status)) {
    errors.status = "Select a valid status.";
  }

  if (!candidateStageOptions.includes(values.stage)) {
    errors.stage = "Select a valid stage.";
  }

  if (values.linkedinUrl && !isValidUrl(values.linkedinUrl)) {
    errors.linkedinUrl = "Enter a valid LinkedIn URL.";
  }

  if (values.cvUrl && !isValidUrl(values.cvUrl)) {
    errors.cvUrl = "Enter a valid CV URL.";
  }

  return errors;
}

export function validateNoteContent(content: string) {
  if (!content.trim()) {
    return "Note content is required.";
  }

  return null;
}

function isValidUrl(value: string) {
  try {
    new URL(value);
    return true;
  } catch {
    return false;
  }
}