import { describe, it, expect, beforeEach, vi } from 'vitest';
import { representativeStorage, RepresentativeStorage } from './localStorage';

describe('representativeStorage', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  const testData: RepresentativeStorage = {
    representatives: [
      {
        id: 'ent-1',
        name: 'Jane Doe',
        entity_type: 'alderman',
        jurisdiction_id: 'jur-1',
      },
    ],
    address: '123 Main St, Chicago, IL',
    districts: ['Ward 1', 'District 5'],
  };

  describe('saveRepresentativeData', () => {
    it('saves data to localStorage', () => {
      representativeStorage.saveRepresentativeData(testData);

      const savedReps = localStorage.getItem('openAdvocacy_userRepresentatives');
      const savedAddress = localStorage.getItem('openAdvocacy_userAddress');
      const savedDistricts = localStorage.getItem('openAdvocacy_userDistricts');

      expect(savedReps).not.toBeNull();
      expect(JSON.parse(savedReps!)).toEqual(testData.representatives);
      expect(savedAddress).toBe(testData.address);
      expect(JSON.parse(savedDistricts!)).toEqual(testData.districts);
    });
  });

  describe('loadRepresentativeData', () => {
    it('loads previously saved data', () => {
      representativeStorage.saveRepresentativeData(testData);
      const loaded = representativeStorage.loadRepresentativeData();

      expect(loaded.representatives).toEqual(testData.representatives);
      expect(loaded.address).toBe(testData.address);
      expect(loaded.districts).toEqual(testData.districts);
    });

    it('returns empty defaults when nothing saved', () => {
      const loaded = representativeStorage.loadRepresentativeData();

      expect(loaded.representatives).toEqual([]);
      expect(loaded.address).toBe('');
      expect(loaded.districts).toEqual([]);
    });
  });

  describe('clearRepresentativeData', () => {
    it('removes all saved data', () => {
      representativeStorage.saveRepresentativeData(testData);
      representativeStorage.clearRepresentativeData();

      const loaded = representativeStorage.loadRepresentativeData();
      expect(loaded.representatives).toEqual([]);
      expect(loaded.address).toBe('');
      expect(loaded.districts).toEqual([]);
    });
  });

  describe('error handling', () => {
    it('handles localStorage errors on save gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => {
        throw new Error('Storage full');
      });

      // Should not throw
      representativeStorage.saveRepresentativeData(testData);
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
      vi.restoreAllMocks();
    });

    it('handles localStorage errors on load gracefully', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => {
        throw new Error('Storage error');
      });

      const loaded = representativeStorage.loadRepresentativeData();
      expect(loaded).toEqual({ representatives: [], address: '', districts: [] });
      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
      vi.restoreAllMocks();
    });
  });
});
