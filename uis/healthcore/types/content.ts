export type ServiceType =
  | "primary_care"
  | "chronic_disease"
  | "preventive"
  | "specialist"
  | "womens_health"
  | "paediatric"
  | "mental_health"
  | "urgent_care"
  | "video_visit";

export interface ClinicLocation {
  locationId: string;
  name: string;
  city: string;
  stateOrCountry: string;
  country: "US" | "UK";
  phone: string;
  addressLine: string;
}

export interface ServiceOffering {
  id: string;
  title: string;
  description: string;
  serviceType: ServiceType;
  ctaLabel: string;
  href: string;
}

export interface ClinicianProfile {
  clinicianId: string;
  fullName: string;
  role: string;
  specialties: string[];
  locationName: string;
  acceptingPatients: boolean;
}

export interface NavItem {
  href: string;
  label: string;
}

export interface PatientSignupFormValues {
  fullName: string;
  email: string;
  phone: string;
  concerns: string;
}

export interface PatientSignupFormErrors {
  fullName?: string;
  email?: string;
  phone?: string;
  concerns?: string;
}
