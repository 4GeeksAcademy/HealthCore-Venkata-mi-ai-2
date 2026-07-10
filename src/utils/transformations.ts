import {
  Appointment,
  Claim,
  Clinician,
  CMEReport,
  CMEStatus,
  Location,
} from "../types";
import {
  addUtcDays,
  daysBetweenCalendar,
  isDateWithinInclusiveRange,
  parseIsoDate,
  roundTo,
  startOfUtcDay,
} from "./_helpers";

function toPercent(numerator: number, denominator: number, decimals: number): number {
  if (denominator === 0) {
    return 0;
  }

  return roundTo((numerator / denominator) * 100, decimals);
}

export function calculateDenialRate(claims: Claim[]): number {
  if (claims.length === 0) {
    throw new Error("Claims array cannot be empty");
  }

  const deniedCount = claims.filter((claim) => claim.status === "denied").length;
  return toPercent(deniedCount, claims.length, 2);
}

export function denialRateByPayer(claims: Claim[]): Record<string, number> {
  const grouped: Record<string, { denied: number; total: number }> = {};

  for (const claim of claims) {
    if (!grouped[claim.payerName]) {
      grouped[claim.payerName] = { denied: 0, total: 0 };
    }

    grouped[claim.payerName].total += 1;
    if (claim.status === "denied") {
      grouped[claim.payerName].denied += 1;
    }
  }

  return Object.entries(grouped).reduce<Record<string, number>>((accumulator, [payer, counts]) => {
    accumulator[payer] = toPercent(counts.denied, counts.total, 2);
    return accumulator;
  }, {});
}

export function denialRateByLocation(claims: Claim[]): Record<string, number> {
  const grouped: Record<string, { denied: number; total: number }> = {};

  for (const claim of claims) {
    if (!grouped[claim.locationId]) {
      grouped[claim.locationId] = { denied: 0, total: 0 };
    }

    grouped[claim.locationId].total += 1;
    if (claim.status === "denied") {
      grouped[claim.locationId].denied += 1;
    }
  }

  return Object.entries(grouped).reduce<Record<string, number>>(
    (accumulator, [locationId, counts]) => {
      accumulator[locationId] = toPercent(counts.denied, counts.total, 2);
      return accumulator;
    },
    {}
  );
}

export function flagHighDenialPayers(claims: Claim[], threshold: number = 8): string[] {
  const rates = denialRateByPayer(claims);
  return Object.entries(rates)
    .filter(([, rate]) => rate > threshold)
    .map(([payer]) => payer);
}

export function calculateNoShowCost(
  appointments: Appointment[],
  location: Location,
  weekEndingDate: string
): number {
  const ending = parseIsoDate(weekEndingDate);
  if (!ending) {
    throw new Error("Invalid weekEndingDate. Expected format YYYY-MM-DD");
  }

  const periodEnd = startOfUtcDay(ending);
  const periodStart = addUtcDays(periodEnd, -6);

  const total = appointments.reduce((sum, appointment) => {
    if (appointment.locationId !== location.locationId || appointment.status !== "no_show") {
      return sum;
    }

    const appointmentDate = parseIsoDate(appointment.scheduledDate);
    if (!appointmentDate) {
      return sum;
    }

    if (!isDateWithinInclusiveRange(appointmentDate, periodStart, periodEnd)) {
      return sum;
    }

    return sum + location.averageConsultationFee[appointment.serviceType];
  }, 0);

  return roundTo(total, 2);
}

export function noShowRateByLocation(appointments: Appointment[]): Record<string, number> {
  const grouped: Record<string, { noShow: number; total: number }> = {};

  for (const appointment of appointments) {
    if (!grouped[appointment.locationId]) {
      grouped[appointment.locationId] = { noShow: 0, total: 0 };
    }

    grouped[appointment.locationId].total += 1;
    if (appointment.status === "no_show") {
      grouped[appointment.locationId].noShow += 1;
    }
  }

  return Object.entries(grouped).reduce<Record<string, number>>(
    (accumulator, [locationId, counts]) => {
      accumulator[locationId] = toPercent(counts.noShow, counts.total, 2);
      return accumulator;
    },
    {}
  );
}

export function flagHighNoShowLocations(
  appointments: Appointment[],
  threshold: number = 20
): string[] {
  const rates = noShowRateByLocation(appointments);
  return Object.entries(rates)
    .filter(([, rate]) => rate > threshold)
    .map(([locationId]) => locationId);
}

function cmeStatusForClinician(clinician: Clinician, asOfDate: Date): {
  complianceStatus: CMEStatus;
  hoursRemaining: number;
  percentComplete: number;
  daysRemainingInCycle: number;
} {
  const hoursRemaining = Math.max(0, clinician.cmeHoursRequired - clinician.cmeHoursLogged);
  const percentComplete =
    clinician.cmeHoursRequired === 0
      ? 100
      : roundTo((clinician.cmeHoursLogged / clinician.cmeHoursRequired) * 100, 1);

  const cycleStart = parseIsoDate(clinician.cmeYearStartDate);
  if (!cycleStart) {
    throw new Error(`Invalid cmeYearStartDate for clinician ${clinician.clinicianId}`);
  }

  const cycleEnd = new Date(
    Date.UTC(cycleStart.getUTCFullYear() + 1, cycleStart.getUTCMonth(), cycleStart.getUTCDate())
  );
  cycleEnd.setUTCDate(cycleEnd.getUTCDate() - 1);
  const daysRemainingInCycle = daysBetweenCalendar(asOfDate, cycleEnd);

  if (clinician.cmeHoursLogged >= clinician.cmeHoursRequired) {
    return {
      complianceStatus: "complete",
      hoursRemaining,
      percentComplete,
      daysRemainingInCycle,
    };
  }

  if (daysRemainingInCycle < 0) {
    return {
      complianceStatus: "overdue",
      hoursRemaining,
      percentComplete,
      daysRemainingInCycle,
    };
  }

  const elapsedDays = Math.max(0, daysBetweenCalendar(cycleStart, asOfDate));
  const cycleLengthDays = Math.max(1, daysBetweenCalendar(cycleStart, cycleEnd));
  const elapsedPercent = roundTo((elapsedDays / cycleLengthDays) * 100, 1);
  const lagPoints = roundTo(elapsedPercent - percentComplete, 1);
  const complianceStatus: CMEStatus = lagPoints > 15 ? "at_risk" : "on_track";

  return {
    complianceStatus,
    hoursRemaining,
    percentComplete,
    daysRemainingInCycle,
  };
}

export function generateCMEReport(clinicians: Clinician[], asOfDate: string): CMEReport[] {
  const asOf = parseIsoDate(asOfDate);
  if (!asOf) {
    throw new Error("Invalid asOfDate. Expected format YYYY-MM-DD");
  }

  return clinicians.map((clinician) => {
    const licenceExpiry = parseIsoDate(clinician.licenceExpiryDate);
    if (!licenceExpiry) {
      throw new Error(`Invalid licenceExpiryDate for clinician ${clinician.clinicianId}`);
    }

    const { complianceStatus, hoursRemaining, percentComplete, daysRemainingInCycle } =
      cmeStatusForClinician(clinician, asOf);

    return {
      clinicianId: clinician.clinicianId,
      fullName: `${clinician.firstName} ${clinician.lastName}`,
      role: clinician.role,
      locationId: clinician.locationId,
      hoursRequired: clinician.cmeHoursRequired,
      hoursLogged: clinician.cmeHoursLogged,
      hoursRemaining,
      percentComplete,
      daysRemainingInCycle,
      complianceStatus,
      licenceExpiryDate: clinician.licenceExpiryDate,
      licenceDaysRemaining: daysBetweenCalendar(asOf, licenceExpiry),
    };
  });
}

export function getCliniciansAtRisk(clinicians: Clinician[], asOfDate: string): Clinician[] {
  const report = generateCMEReport(clinicians, asOfDate);
  const ids = new Set(
    report
      .filter((entry) => entry.complianceStatus === "at_risk" || entry.complianceStatus === "overdue")
      .map((entry) => entry.clinicianId)
  );

  return clinicians.filter((clinician) => ids.has(clinician.clinicianId));
}

export function getCliniciansWithExpiringLicences(
  clinicians: Clinician[],
  asOfDate: string,
  daysThreshold: number = 90
): Clinician[] {
  const asOf = parseIsoDate(asOfDate);
  if (!asOf) {
    throw new Error("Invalid asOfDate. Expected format YYYY-MM-DD");
  }

  return clinicians.filter((clinician) => {
    const expiry = parseIsoDate(clinician.licenceExpiryDate);
    if (!expiry) {
      return false;
    }

    const daysRemaining = daysBetweenCalendar(asOf, expiry);
    return daysRemaining >= 0 && daysRemaining <= daysThreshold;
  });
}
