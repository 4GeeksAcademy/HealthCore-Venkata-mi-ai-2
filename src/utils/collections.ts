import { Appointment, AppointmentStatus, Claim } from "../types";

export function filterClaims(
  claims: Claim[],
  filters: Partial<Pick<Claim, "locationId" | "status" | "payerName" | "serviceType">>
): Claim[] {
  const keys = Object.keys(filters) as Array<keyof typeof filters>;

  return claims.filter((claim) =>
    keys.every((key) => filters[key] === undefined || claim[key] === filters[key])
  );
}

export function filterAppointmentsByStatus(
  appointments: Appointment[],
  status: AppointmentStatus[]
): Appointment[] {
  const allowed = new Set(status);
  return appointments.filter((appointment) => allowed.has(appointment.status));
}

export function sortClaimsById(claims: Claim[], direction: "asc" | "desc"): Claim[] {
  const sorted = [...claims].sort((a, b) => a.claimId.localeCompare(b.claimId));
  return direction === "asc" ? sorted : sorted.reverse();
}

export function sortAppointmentsByDate(
  appointments: Appointment[],
  direction: "asc" | "desc"
): Appointment[] {
  const sorted = [...appointments].sort((a, b) => a.scheduledDate.localeCompare(b.scheduledDate));
  return direction === "asc" ? sorted : sorted.reverse();
}

export function groupClaimsBy(
  claims: Claim[],
  key: "locationId" | "payerName" | "status" | "serviceType"
): Record<string, Claim[]> {
  return claims.reduce<Record<string, Claim[]>>((accumulator, claim) => {
    const groupKey = claim[key];
    if (!accumulator[groupKey]) {
      accumulator[groupKey] = [];
    }

    accumulator[groupKey].push(claim);
    return accumulator;
  }, {});
}
