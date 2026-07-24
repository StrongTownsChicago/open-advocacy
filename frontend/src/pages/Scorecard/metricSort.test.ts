import { describe, it, expect } from 'vitest';
import { compareByMetric } from './metricSort';
import { EntityStatus, ScorecardEntityRow } from '../../types';

function row(name: string, metrics?: Record<string, number | string | null>): ScorecardEntityRow {
  return {
    entity: {
      id: `id-${name}`,
      name,
      entity_type: 'alderperson',
      jurisdiction_id: 'jur-1',
    },
    statuses: { 'project-1': { status: EntityStatus.UNKNOWN, label: 'Unknown' } },
    aligned_count: 0,
    total_scoreable: 1,
    ...(metrics ? { metrics } : {}),
  };
}

describe('compareByMetric', () => {
  it('orders numerically ascending', () => {
    expect(compareByMetric(row('a', { d: 10 }), row('b', { d: 20 }), 'd')).toBeLessThan(0);
    expect(compareByMetric(row('a', { d: 20 }), row('b', { d: 10 }), 'd')).toBeGreaterThan(0);
  });

  it('returns 0 for equal values', () => {
    expect(compareByMetric(row('a', { d: 5 }), row('b', { d: 5 }), 'd')).toBe(0);
  });

  it('compares numerically, not lexicographically', () => {
    // "9" > "10" lexicographically but 9 < 10 numerically
    expect(compareByMetric(row('a', { d: 9 }), row('b', { d: 10 }), 'd')).toBeLessThan(0);
  });

  it('coerces numeric strings', () => {
    expect(compareByMetric(row('a', { d: '9.5' }), row('b', { d: '10' }), 'd')).toBeLessThan(0);
    expect(compareByMetric(row('a', { d: '10' }), row('b', { d: 10 }), 'd')).toBe(0);
  });

  it('treats null as -Infinity (sorts last descending)', () => {
    expect(compareByMetric(row('a', { d: null }), row('b', { d: 0 }), 'd')).toBeLessThan(0);
  });

  it('treats a missing key as -Infinity', () => {
    expect(compareByMetric(row('a', { other: 1 }), row('b', { d: -100 }), 'd')).toBeLessThan(0);
  });

  it('treats a completely missing metrics object as -Infinity', () => {
    expect(compareByMetric(row('a'), row('b', { d: -100 }), 'd')).toBeLessThan(0);
  });

  it('treats non-numeric strings as -Infinity', () => {
    expect(compareByMetric(row('a', { d: 'n/a' }), row('b', { d: -100 }), 'd')).toBeLessThan(0);
  });

  it('returns 0 when both rows lack the metric', () => {
    expect(compareByMetric(row('a'), row('b'), 'd')).toBe(0);
    expect(compareByMetric(row('a', { d: null }), row('b'), 'd')).toBe(0);
  });

  it('sorts a list into ascending numeric order with missing values first', () => {
    const rows = [row('c', { d: 30 }), row('m'), row('a', { d: 5 }), row('b', { d: 12 })];
    const sorted = [...rows].sort((x, y) => compareByMetric(x, y, 'd'));
    expect(sorted.map(r => r.entity.name)).toEqual(['m', 'a', 'b', 'c']);
  });
});
