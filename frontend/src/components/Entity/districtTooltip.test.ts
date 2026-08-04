import { describe, it, expect } from 'vitest';
import { buildDistrictTooltip } from './districtTooltip';
import { Entity, EntityStatus, EntityStatusRecord, MetricDisplayConfig } from '../../types';

const entity = { id: 'e1', name: 'Scott Waguespack' } as Entity;

const record = (metadata: Record<string, unknown>) =>
  ({
    entity_id: 'e1',
    status: EntityStatus.LEANING_APPROVAL,
    notes: 'A long status note that should never reach the map tooltip.',
    record_metadata: metadata,
  }) as unknown as EntityStatusRecord;

const METRICS: MetricDisplayConfig[] = [
  { key: 'restrictions', label: 'Restrictions', format: 'text' },
  { key: 'adu_coverage_pct', label: 'ADU-eligible', format: 'percentage' },
];

const base = {
  districtName: 'Ward 32',
  entity,
  statusLabel: 'Whole ward — with restrictions',
  statusColor: '#65a30d',
  metrics: METRICS,
};

describe('buildDistrictTooltip', () => {
  it('shows the district, representative and status', () => {
    const html = buildDistrictTooltip({ ...base, record: record({}) });
    expect(html).toContain('Ward 32');
    expect(html).toContain('Scott Waguespack');
    expect(html).toContain('Whole ward — with restrictions');
  });

  it('never includes the status note — that belongs in the table row', () => {
    const html = buildDistrictTooltip({ ...base, record: record({}) });
    expect(html).not.toContain('should never reach the map tooltip');
  });

  it('renders metrics that have values', () => {
    const html = buildDistrictTooltip({
      ...base,
      record: record({ restrictions: 'Block cap, Owner occupancy', adu_coverage_pct: 100 }),
    });
    expect(html).toContain('Block cap');
    expect(html).toContain('Owner occupancy');
    expect(html).toContain('100.0%');
  });

  it('renders a comma-separated text value as separate pills', () => {
    const html = buildDistrictTooltip({
      ...base,
      record: record({ restrictions: 'Block cap, Owner occupancy, Admin adjustment' }),
    });
    expect(html).toContain('<span class="dt-tag">Block cap</span>');
    expect(html).toContain('<span class="dt-tag">Admin adjustment</span>');
    expect(html).not.toContain('dt-val');
  });

  it('keeps a single-item text value as plain text, not a pill', () => {
    const html = buildDistrictTooltip({ ...base, record: record({ restrictions: 'None' }) });
    expect(html).toContain('<span class="dt-val">None</span>');
    expect(html).not.toContain('dt-tag');
  });

  it('does not split numeric values on commas', () => {
    const html = buildDistrictTooltip({
      ...base,
      metrics: [{ key: 'n', label: 'Population', format: 'number' }],
      record: record({ n: 1234567 }),
    });
    expect(html).not.toContain('dt-tag');
    expect(html).toContain('1,234,567');
  });

  it('omits metrics with no value rather than printing an em dash', () => {
    const html = buildDistrictTooltip({
      ...base,
      record: record({ restrictions: '—', adu_coverage_pct: 0 }),
    });
    expect(html).not.toContain('Restrictions');
    expect(html).toContain('ADU-eligible');
  });

  it('omits the metrics block entirely when nothing has a value', () => {
    const html = buildDistrictTooltip({ ...base, record: record({}) });
    expect(html).not.toContain('dt-rows');
  });

  it('escapes representative names', () => {
    const html = buildDistrictTooltip({
      ...base,
      entity: { id: 'e1', name: '<img onerror=alert(1)>' } as Entity,
      record: record({}),
    });
    expect(html).toContain('&lt;img onerror=alert(1)&gt;');
    expect(html).not.toContain('<img');
  });

  it('handles a district with no representative', () => {
    const html = buildDistrictTooltip({ ...base, entity: undefined, record: undefined });
    expect(html).toContain('Ward 32');
    expect(html).not.toContain('dt-status');
  });
});
