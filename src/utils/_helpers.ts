export function roundTo(value: number, decimals: number): number {
  const factor = 10 ** decimals;
  return Math.round((value + Number.EPSILON) * factor) / factor;
}

export function parseIsoDate(dateString: string): Date | null {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(dateString)) {
    return null;
  }

  const parsed = new Date(`${dateString}T00:00:00Z`);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }

  return parsed;
}

export function startOfUtcDay(date: Date): Date {
  return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), date.getUTCDate()));
}

export function daysBetweenCalendar(startDate: Date, endDate: Date): number {
  const millisecondsPerDay = 24 * 60 * 60 * 1000;
  const start = startOfUtcDay(startDate).getTime();
  const end = startOfUtcDay(endDate).getTime();
  return Math.floor((end - start) / millisecondsPerDay);
}

export function addUtcDays(date: Date, days: number): Date {
  const next = new Date(date.getTime());
  next.setUTCDate(next.getUTCDate() + days);
  return startOfUtcDay(next);
}

export function isDateWithinInclusiveRange(date: Date, start: Date, end: Date): boolean {
  const target = startOfUtcDay(date).getTime();
  const rangeStart = startOfUtcDay(start).getTime();
  const rangeEnd = startOfUtcDay(end).getTime();
  return target >= rangeStart && target <= rangeEnd;
}

export function isValidIsoDateString(dateString: string): boolean {
  return parseIsoDate(dateString) !== null;
}

export function parseIsoDateTime(value: string): Date | null {
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
}
