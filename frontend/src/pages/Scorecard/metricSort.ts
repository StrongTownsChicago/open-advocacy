import { ScorecardEntityRow } from '../../types';

/**
 * Numeric comparison of two scorecard rows on an arbitrary metric key.
 *
 * Values are coerced with parseFloat; missing, null, or non-numeric values sort
 * as -Infinity so that rows without data always land at the bottom of a
 * descending sort (mirrors components/Entity/entitySort.ts).
 *
 * Returns a negative number when `a` sorts before `b` ascending.
 */
export function compareByMetric(a: ScorecardEntityRow, b: ScorecardEntityRow, key: string): number {
  const aVal = toNumber(a.metrics?.[key]);
  const bVal = toNumber(b.metrics?.[key]);
  if (aVal === bVal) return 0;
  return aVal < bVal ? -1 : 1;
}

function toNumber(raw: number | string | null | undefined): number {
  if (raw == null) return -Infinity;
  const parsed = parseFloat(String(raw));
  return Number.isNaN(parsed) ? -Infinity : parsed;
}
