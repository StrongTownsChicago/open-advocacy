import { MetricDisplayConfig } from '../../types';

/**
 * Metrics that should be rendered as scorecard columns / caption lines.
 *
 * `show_in_table` is opt-out: a metric with the flag omitted is shown, a metric
 * with `show_in_table: false` is declared (so its values still arrive) but not
 * displayed.
 */
export function visibleMetrics(metrics: MetricDisplayConfig[] | undefined): MetricDisplayConfig[] {
  return (metrics ?? []).filter(metric => metric.show_in_table !== false);
}
