export const EMPTY_METRIC_LABEL = '—';

/** Formatting seam — additional variants (percent, currency, …) plug in here. */
const METRIC_FORMATTERS: Record<string, (value: number) => string> = {
  number: value => value.toLocaleString(),
};

/**
 * Format a metric value for display.
 *
 * Null/undefined values render as an em dash. Numbers (and numeric strings) are
 * rendered with locale grouping. The `format` argument is a seam for future
 * variants; unknown formats fall back to default number formatting.
 */
export function formatMetricValue(
  value: number | string | null | undefined,
  format?: string
): string {
  if (value == null) return EMPTY_METRIC_LABEL;
  const numeric = typeof value === 'number' ? value : parseFloat(value);
  if (Number.isNaN(numeric)) {
    // Non-numeric strings pass through as-is; blank strings render as an em dash.
    return typeof value === 'string' && value.trim() !== '' ? value : EMPTY_METRIC_LABEL;
  }
  const formatter = (format && METRIC_FORMATTERS[format]) || METRIC_FORMATTERS.number;
  return formatter(numeric);
}
