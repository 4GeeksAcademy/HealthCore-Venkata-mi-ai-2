export const INCIDENT_STATUSES = [
  { value: "open", label: "Open" },
  { value: "in_progress", label: "In progress" },
  { value: "resolved", label: "Resolved" },
  { value: "discarded", label: "Discarded" },
] as const;

export const INCIDENT_ORIGINS = [
  { value: "customer", label: "Customer" },
  { value: "branch", label: "Branch" },
  { value: "internal", label: "Internal" },
] as const;

export const INCIDENT_CATEGORIES = [
  { value: "clinical_equipment", label: "Clinical equipment" },
  { value: "it_system", label: "IT system" },
  { value: "billing_error", label: "Billing error" },
  { value: "compliance_breach", label: "Compliance breach" },
  { value: "patient_experience", label: "Patient experience" },
  { value: "staff_issue", label: "Staff issue" },
  { value: "facility_issue", label: "Facility issue" },
  { value: "referral_issue", label: "Referral issue" },
  { value: "other", label: "Other" },
] as const;

export const INCIDENT_BRANCHES = [
  { value: "central", label: "Central — Austin Main Clinic" },
  { value: "austin_north", label: "Austin — North" },
  { value: "dallas_uptown", label: "Dallas Uptown" },
  { value: "houston_med_center", label: "Houston Medical Center" },
  { value: "san_antonio_west", label: "San Antonio West" },
  { value: "miami_brickell", label: "Miami Brickell" },
  { value: "miami_doral", label: "Miami Doral" },
  { value: "orlando_east", label: "Orlando East" },
  { value: "tampa_bay", label: "Tampa Bay" },
  { value: "atlanta_midtown", label: "Atlanta Midtown" },
  { value: "savannah", label: "Savannah" },
  { value: "london_city", label: "London City" },
  { value: "london_west", label: "London West End" },
  { value: "manchester_central", label: "Manchester Central" },
] as const;

export type IncidentStatus = (typeof INCIDENT_STATUSES)[number]["value"];
export type IncidentOrigin = (typeof INCIDENT_ORIGINS)[number]["value"];
export type IncidentCategory = (typeof INCIDENT_CATEGORIES)[number]["value"];
export type IncidentBranch = (typeof INCIDENT_BRANCHES)[number]["value"];

export const NEXT_STATUSES: Record<IncidentStatus, IncidentStatus[]> = {
  open: ["in_progress", "discarded"],
  in_progress: ["resolved", "discarded"],
  resolved: [],
  discarded: [],
};

export function branchLabel(value: string): string {
  return INCIDENT_BRANCHES.find((b) => b.value === value)?.label ?? value;
}

export function statusLabel(value: string): string {
  return INCIDENT_STATUSES.find((s) => s.value === value)?.label ?? value;
}
