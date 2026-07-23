import type {
  PatientSignupFormErrors,
  PatientSignupFormValues,
} from "@/types/content";

const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const phonePattern = /^[+]?[\d\s().-]{7,20}$/;

export function validatePatientSignup(
  values: PatientSignupFormValues,
): PatientSignupFormErrors {
  const errors: PatientSignupFormErrors = {};

  if (!values.fullName.trim()) {
    errors.fullName = "Full name is required.";
  }

  if (!values.email.trim()) {
    errors.email = "Email address is required.";
  } else if (!emailPattern.test(values.email.trim())) {
    errors.email = "Enter a valid email address.";
  }

  if (!values.phone.trim()) {
    errors.phone = "Phone number is required.";
  } else if (!phonePattern.test(values.phone.trim())) {
    errors.phone = "Enter a valid phone number.";
  }

  if (!values.concerns.trim()) {
    errors.concerns = "Tell us briefly how we can help.";
  }

  return errors;
}
