import { Entity, EntityStatusRecord, MetricDisplayConfig } from '../../types';
import { formatMetricValue } from '../../utils/dataTransformers';
import { escapeHtml } from '../../utils/html';

export interface DistrictTooltipInput {
  districtName: string;
  entity?: Entity;
  record?: EntityStatusRecord;
  statusLabel: string;
  statusColor: string;
  metrics: MetricDisplayConfig[];
}

/**
 * Build the HTML for a district hover tooltip.
 *
 * Kept deliberately sparse: a map tooltip is glanced at, not read. It carries
 * the district, who represents it, the status, and any metrics flagged for the
 * tooltip -- and nothing else. Longer prose (the status note) lives in the
 * table row, where there is room for it.
 */
export const buildDistrictTooltip = ({
  districtName,
  entity,
  record,
  statusLabel,
  statusColor,
  metrics,
}: DistrictTooltipInput): string => {
  const rows = metrics
    .map(metric => {
      const value = record?.record_metadata?.[metric.key];
      if (value === null || value === undefined || value === '') return '';
      const format = metric.format ?? 'text';
      const formatted = formatMetricValue(value, format);
      if (formatted === '—') return '';

      // A comma-separated text value reads better as pills: each item stays
      // whole instead of wrapping mid-phrase ("Admin / adjustment").
      const parts = format === 'text' ? formatted.split(', ').filter(Boolean) : [];
      const rendered =
        parts.length > 1
          ? `<span class="dt-tags">` +
            parts.map(p => `<span class="dt-tag">${escapeHtml(p)}</span>`).join('') +
            `</span>`
          : `<span class="dt-val">${escapeHtml(formatted)}</span>`;

      return (
        `<div class="dt-row">` +
        `<span class="dt-key">${escapeHtml(metric.label)}</span>` +
        rendered +
        `</div>`
      );
    })
    .join('');

  const subtitle = entity ? `<div class="dt-sub">${escapeHtml(entity.name)}</div>` : '';

  const status = entity
    ? `<div class="dt-status" style="color:${escapeHtml(statusColor)}">` +
      `${escapeHtml(statusLabel)}</div>`
    : '';

  return (
    `<div class="dt">` +
    `<div class="dt-title">` +
    `<span class="dt-dot" style="background:${escapeHtml(statusColor)}"></span>` +
    `${escapeHtml(districtName)}` +
    `</div>` +
    subtitle +
    status +
    (rows ? `<div class="dt-rows">${rows}</div>` : '') +
    `</div>`
  );
};
