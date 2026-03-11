import api from './api';

export interface ImportLocation {
  key: string;
  name: string;
  description?: string;
}

export interface ImportResult {
  location: string;
  steps_completed: number;
  steps_failed: number;
  details: Record<string, unknown>;
}

export const importsService = {
  async getLocations(): Promise<{ data: ImportLocation[] }> {
    return api.get<ImportLocation[]>('/imports/locations');
  },

  async triggerImport(locationKey: string): Promise<{ data: ImportResult }> {
    return api.post<ImportResult>(`/imports/locations/${encodeURIComponent(locationKey)}`);
  },
};
