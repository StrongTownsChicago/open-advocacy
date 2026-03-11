import { describe, it, expect } from 'vitest';
import { getStatusColor, getStatusLabel } from './statusColors';
import { EntityStatus } from '../types';

describe('getStatusColor', () => {
  it('returns distinct colors for all defined statuses', () => {
    const colors = new Set([
      getStatusColor(EntityStatus.SOLID_APPROVAL),
      getStatusColor(EntityStatus.LEANING_APPROVAL),
      getStatusColor(EntityStatus.NEUTRAL),
      getStatusColor(EntityStatus.LEANING_DISAPPROVAL),
      getStatusColor(EntityStatus.SOLID_DISAPPROVAL),
    ]);
    // All 5 non-unknown statuses should have unique colors
    expect(colors.size).toBe(5);
  });

  it('returns a color for every EntityStatus value', () => {
    for (const status of Object.values(EntityStatus)) {
      const color = getStatusColor(status);
      expect(color).toMatch(/^#[0-9a-f]{6}/i);
    }
  });

  it('returns grey for UNKNOWN status (default case)', () => {
    const color = getStatusColor(EntityStatus.UNKNOWN);
    expect(color).toBe('#9e9e9e');
  });
});

describe('getStatusLabel', () => {
  it('returns human-readable labels for all defined statuses', () => {
    expect(getStatusLabel(EntityStatus.SOLID_APPROVAL)).toBe('Solid Approval');
    expect(getStatusLabel(EntityStatus.LEANING_APPROVAL)).toBe('Leaning Approval');
    expect(getStatusLabel(EntityStatus.NEUTRAL)).toBe('Neutral');
    expect(getStatusLabel(EntityStatus.LEANING_DISAPPROVAL)).toBe('Leaning Disapproval');
    expect(getStatusLabel(EntityStatus.SOLID_DISAPPROVAL)).toBe('Solid Disapproval');
  });

  it('returns "Unknown" for UNKNOWN status', () => {
    expect(getStatusLabel(EntityStatus.UNKNOWN)).toBe('Unknown');
  });

  it('returns "Unknown" for unrecognized status values', () => {
    expect(getStatusLabel('not_a_real_status' as EntityStatus)).toBe('Unknown');
  });
});
