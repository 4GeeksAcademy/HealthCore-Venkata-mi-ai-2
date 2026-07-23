import type {
  ClinicLocation,
  ClinicianProfile,
  NavItem,
  ServiceOffering,
} from "@/types/content";

export const siteBrand = {
  name: "HealthCore",
  tagline: "Advanced, Simplified Healthcare",
  phoneDisplay: "1-800-555-0199",
  phoneHref: "tel:+18005550199",
  address: "701 Brazos Street, Austin, TX 78701",
} as const;

export const primaryNav: NavItem[] = [
  { href: "/doctors", label: "Doctors" },
  { href: "/locations", label: "Locations" },
  { href: "/services", label: "Services & Specialties" },
  { href: "/costs", label: "Costs & Billing" },
  { href: "/care", label: "Get Care Now" },
  { href: "/about", label: "About HealthCore" },
];

export const clinics: ClinicLocation[] = [
  {
    locationId: "us-tx-001",
    name: "HealthCore Austin Central",
    city: "Austin",
    stateOrCountry: "TX",
    country: "US",
    phone: "(512) 340-8800",
    addressLine: "701 Brazos Street, Austin, TX 78701",
  },
  {
    locationId: "us-fl-001",
    name: "HealthCore Miami",
    city: "Miami",
    stateOrCountry: "FL",
    country: "US",
    phone: "(305) 510-7700",
    addressLine: "100 Biscayne Blvd, Miami, FL 33132",
  },
  {
    locationId: "us-ga-001",
    name: "HealthCore Atlanta",
    city: "Atlanta",
    stateOrCountry: "GA",
    country: "US",
    phone: "(404) 330-9900",
    addressLine: "191 Peachtree St NE, Atlanta, GA 30303",
  },
  {
    locationId: "uk-lon-001",
    name: "HealthCore London",
    city: "London",
    stateOrCountry: "UK",
    country: "UK",
    phone: "+44 20 7946 0100",
    addressLine: "1 Canada Square, London E14 5AB",
  },
  {
    locationId: "uk-man-001",
    name: "HealthCore Manchester",
    city: "Manchester",
    stateOrCountry: "UK",
    country: "UK",
    phone: "+44 161 496 0100",
    addressLine: "1 Spinningfields, Manchester M3 3EB",
  },
];

export const services: ServiceOffering[] = [
  {
    id: "primary",
    title: "Primary Care",
    description:
      "In-person and video visits with HealthCore primary care clinicians for everyday health needs across our US and UK clinics.",
    serviceType: "primary_care",
    ctaLabel: "Find a provider",
    href: "/doctors",
  },
  {
    id: "urgent",
    title: "Urgent Care",
    description:
      "Walk-in and same-day appointments so patients can get back to what matters — typically in about 30 minutes.",
    serviceType: "urgent_care",
    ctaLabel: "Save my spot",
    href: "/care",
  },
  {
    id: "video",
    title: "On-Demand Video Visits",
    description:
      "Secure video urgent care from home, coordinated with the same HealthCore clinical standards as clinic visits.",
    serviceType: "video_visit",
    ctaLabel: "Get started",
    href: "/care",
  },
  {
    id: "chronic",
    title: "Chronic Disease Management",
    description:
      "Ongoing support for chronic conditions with care plans aligned to clinic operations and payer requirements.",
    serviceType: "chronic_disease",
    ctaLabel: "Explore services",
    href: "/services",
  },
  {
    id: "preventive",
    title: "Preventive Health",
    description:
      "Screenings and wellness visits that keep HealthCore patients informed and ahead of preventable risk.",
    serviceType: "preventive",
    ctaLabel: "Learn more",
    href: "/services",
  },
  {
    id: "mental",
    title: "Mental Health",
    description:
      "Outpatient mental health support integrated with primary and specialty care across the network.",
    serviceType: "mental_health",
    ctaLabel: "Get care now",
    href: "/care",
  },
];

export const clinicians: ClinicianProfile[] = [
  {
    clinicianId: "CLN-000101",
    fullName: "Dr. Amara Okonkwo",
    role: "Physician",
    specialties: ["Primary care", "Preventive health"],
    locationName: "HealthCore Austin Central",
    acceptingPatients: true,
  },
  {
    clinicianId: "CLN-000214",
    fullName: "Jordan Miles, NP",
    role: "Nurse Practitioner",
    specialties: ["Urgent care", "Women's health"],
    locationName: "HealthCore Miami",
    acceptingPatients: true,
  },
  {
    clinicianId: "CLN-000330",
    fullName: "Dr. Priya Shah",
    role: "Physician",
    specialties: ["Chronic disease", "Specialist consults"],
    locationName: "HealthCore Atlanta",
    acceptingPatients: false,
  },
  {
    clinicianId: "CLN-000418",
    fullName: "Sam Patel, RN",
    role: "Nurse",
    specialties: ["Paediatric", "Video visits"],
    locationName: "HealthCore London",
    acceptingPatients: true,
  },
];
