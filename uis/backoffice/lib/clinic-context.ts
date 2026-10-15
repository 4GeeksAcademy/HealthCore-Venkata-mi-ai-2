/** Default clinic context for CONTEXT-healthcore inventory telemetry (no PHI). */

export const DEFAULT_CLINIC_ID = "us-tx-001";
export const DEFAULT_COUNTRY = "US";
export const DEFAULT_DEPARTMENT = "general_consultation";
export const EXPIRY_FLAG_DAYS = 30;

export function daysToExpiry(expiryDate: string | null | undefined): number | null {
  if (!expiryDate) return null;
  const expiry = new Date(`${expiryDate}T00:00:00Z`);
  if (Number.isNaN(expiry.getTime())) return null;
  const today = new Date();
  const utcToday = Date.UTC(today.getUTCFullYear(), today.getUTCMonth(), today.getUTCDate());
  const diff = Math.floor((expiry.getTime() - utcToday) / 86_400_000);
  return diff;
}

export function shouldFlagExpiry(expiryDate: string | null | undefined): boolean {
  const days = daysToExpiry(expiryDate);
  return days !== null && days >= 0 && days <= EXPIRY_FLAG_DAYS;
}
