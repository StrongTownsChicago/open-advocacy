import { describe, it, expect } from 'vitest';
import { compareDistrictNames } from './districtSort';

describe('compareDistrictNames', () => {
  it('sorts numerically: Ward 2 before Ward 10', () => {
    expect(compareDistrictNames('Ward 2', 'Ward 10')).toBeLessThan(0);
  });

  it('sorts numerically: Ward 10 after Ward 2', () => {
    expect(compareDistrictNames('Ward 10', 'Ward 2')).toBeGreaterThan(0);
  });

  it('returns 0 for equal ward names', () => {
    expect(compareDistrictNames('Ward 5', 'Ward 5')).toBe(0);
  });

  it('falls back to localeCompare for non-numeric names', () => {
    const result = compareDistrictNames('Alpha', 'Beta');
    expect(result).toBe('Alpha'.localeCompare('Beta'));
  });

  it('falls back to localeCompare when one name has no number', () => {
    const result = compareDistrictNames('Ward 3', 'Beta');
    expect(result).toBe('Ward 3'.localeCompare('Beta'));
  });

  it('treats null as empty string and falls back to localeCompare', () => {
    const result = compareDistrictNames(null, 'Ward 1');
    expect(result).toBe(''.localeCompare('Ward 1'));
  });

  it('returns 0 when both are undefined', () => {
    expect(compareDistrictNames(undefined, undefined)).toBe(0);
  });

  it('sorts numerically: District 12 after District 2', () => {
    expect(compareDistrictNames('District 12', 'District 2')).toBeGreaterThan(0);
  });
});
