import { describe, it, expect } from 'vitest';
import {
  getStatusColor,
  getStatusLabel,
  makeStatusColorFn,
  makeStatusLabelFn,
} from './statusColors';
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
    expect(color).toBe('#94a3b8');
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

describe('makeStatusLabelFn', () => {
  it('returns default labels when no custom labels provided', () => {
    const fn = makeStatusLabelFn();
    expect(fn(EntityStatus.SOLID_APPROVAL)).toBe('Solid Approval');
    expect(fn(EntityStatus.LEANING_DISAPPROVAL)).toBe('Leaning Disapproval');
  });

  it('uses custom label when provided for a status', () => {
    const fn = makeStatusLabelFn({ solid_approval: 'Fully Opted In' });
    expect(fn(EntityStatus.SOLID_APPROVAL)).toBe('Fully Opted In');
  });

  it('falls back to default for statuses not in the custom map', () => {
    const fn = makeStatusLabelFn({ solid_approval: 'Fully Opted In' });
    expect(fn(EntityStatus.LEANING_APPROVAL)).toBe('Leaning Approval');
    expect(fn(EntityStatus.NEUTRAL)).toBe('Neutral');
  });

  it('supports a full custom label map', () => {
    const customLabels = {
      solid_approval: 'Fully Opted In',
      leaning_approval: 'Partially Opted In',
      neutral: 'Not Eligible',
      leaning_disapproval: 'Not Opted In',
      solid_disapproval: 'Strongly Opposed',
      unknown: 'Unknown',
    };
    const fn = makeStatusLabelFn(customLabels);
    expect(fn(EntityStatus.SOLID_APPROVAL)).toBe('Fully Opted In');
    expect(fn(EntityStatus.LEANING_DISAPPROVAL)).toBe('Not Opted In');
    expect(fn(EntityStatus.NEUTRAL)).toBe('Not Eligible');
  });

  it('falls back to default when custom label is an empty string', () => {
    const fn = makeStatusLabelFn({ solid_approval: '' });
    expect(fn(EntityStatus.SOLID_APPROVAL)).toBe('Solid Approval');
  });
});

describe('makeStatusColorFn', () => {
  it('falls back to the default palette when no overrides are given', () => {
    const fn = makeStatusColorFn();
    expect(fn(EntityStatus.SOLID_APPROVAL)).toBe(getStatusColor(EntityStatus.SOLID_APPROVAL));
  });

  it('uses an override when one is supplied', () => {
    const fn = makeStatusColorFn({ neutral: '#eab308' });
    expect(fn(EntityStatus.NEUTRAL)).toBe('#eab308');
  });

  it('falls back per-status for entries with no override', () => {
    const fn = makeStatusColorFn({ neutral: '#eab308' });
    expect(fn(EntityStatus.SOLID_DISAPPROVAL)).toBe(
      getStatusColor(EntityStatus.SOLID_DISAPPROVAL)
    );
  });

  it('supports the ADU dashboard ramp, which recolors neutral as a mid-scale value', () => {
    const aduColors = {
      solid_approval: '#166534',
      leaning_approval: '#65a30d',
      neutral: '#eab308',
      leaning_disapproval: '#f97316',
      solid_disapproval: '#dc2626',
      unknown: '#94a3b8',
    };
    const fn = makeStatusColorFn(aduColors);
    const ramp = [
      EntityStatus.SOLID_APPROVAL,
      EntityStatus.LEANING_APPROVAL,
      EntityStatus.NEUTRAL,
      EntityStatus.LEANING_DISAPPROVAL,
      EntityStatus.SOLID_DISAPPROVAL,
    ].map(fn);
    expect(new Set(ramp).size).toBe(5);
  });

  it('falls back to default when a custom color is an empty string', () => {
    const fn = makeStatusColorFn({ neutral: '' });
    expect(fn(EntityStatus.NEUTRAL)).toBe(getStatusColor(EntityStatus.NEUTRAL));
  });
});
