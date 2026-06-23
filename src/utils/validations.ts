import { Claim, Clinician } from "../types";
import { isValidIsoDateString, parseIsoDate, roundTo } from "./_helpers";

type ValidationResult = { valid: boolean; errors: string[] };

const VALID_ROLES = new Set([
  "physician",
  "nurse_practitioner",
  "nurse",
  "medical_assistant",
]);

export function validateClaim(claim: Claim, knownLocationIds: string[]): ValidationResult {
  const errors: string[] = [];

  if (claim.claimAmount <= 0) {
    errors.push("claimAmount must be greater than 0");
  }

  const submissionDate = parseIsoDate(claim.submissionDate);
  if (!submissionDate) {
    errors.push("submissionDate must be a valid ISO date string (YYYY-MM-DD)");
  } else {
    const today = parseIsoDate(new Date().toISOString().slice(0, 10));
    if (today && submissionDate.getTime() > today.getTime()) {
      errors.push("submissionDate must not be in the future");
    }
  }

  if (!knownLocationIds.includes(claim.locationId)) {
    errors.push("locationId must match one of the known clinic IDs");
  }

  if (claim.status === "denied" && !claim.denialReason) {
    errors.push("denialReason is required when claim status is denied");
  }

  if (!/^HC-[A-Za-z0-9]{6}$/.test(claim.patientId)) {
    errors.push("patientId must match the format HC- followed by 6 alphanumeric characters");
  }

  return { valid: errors.length === 0, errors };
}

export function validateClinician(clinician: Clinician): ValidationResult {
  const errors: string[] = [];

  if (clinician.cmeHoursRequired < 0) {
    errors.push("cmeHoursRequired must be greater than or equal to 0");
  }

  if (clinician.cmeHoursLogged < 0) {
    errors.push("cmeHoursLogged must be greater than or equal to 0");
  }

  if (!VALID_ROLES.has(clinician.role)) {
    errors.push("role must be one of physician, nurse_practitioner, nurse, medical_assistant");
  }

  if (!isValidIsoDateString(clinician.licenceExpiryDate)) {
    errors.push("licenceExpiryDate must be a valid ISO date string (YYYY-MM-DD)");
  } else {
    const today = parseIsoDate(new Date().toISOString().slice(0, 10));
    const expiry = parseIsoDate(clinician.licenceExpiryDate);
    if (today && expiry && expiry.getTime() < today.getTime()) {
      errors.push("licenceExpiryDate is in the past and the licence is expired");
    }
  }

  return { valid: errors.length === 0, errors };
}

export function isDenialRateAboveThreshold(rate: number, threshold: number = 8): boolean {
  return roundTo(rate, 2) > threshold;
}

export function isNoShowRateAboveThreshold(rate: number, threshold: number = 20): boolean {
  return roundTo(rate, 2) > threshold;
}
