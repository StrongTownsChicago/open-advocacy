import { describe, it, expect } from 'vitest';
import { visibleMetrics } from './metricDisplay';

describe('visibleMetrics', () => {
  it('returns an empty list when metrics are undefined', () => {
    expect(visibleMetrics(undefined)).toEqual([]);
  });

  it('keeps metrics without an explicit show_in_table flag', () => {
    const metrics = [{ key: 'a', label: 'A' }];
    expect(visibleMetrics(metrics)).toEqual(metrics);
  });

  it('keeps metrics with show_in_table true and drops false', () => {
    const metrics = [
      { key: 'a', label: 'A', show_in_table: true },
      { key: 'b', label: 'B', show_in_table: false },
      { key: 'c', label: 'C' },
    ];
    expect(visibleMetrics(metrics).map(m => m.key)).toEqual(['a', 'c']);
  });

  it('preserves declaration order', () => {
    const metrics = [
      { key: 'z', label: 'Z' },
      { key: 'a', label: 'A' },
    ];
    expect(visibleMetrics(metrics).map(m => m.key)).toEqual(['z', 'a']);
  });
});
