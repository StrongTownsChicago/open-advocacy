import api from './api';
import { Jurisdiction } from '../types';

interface JurisdictionCreateData {
  name: string;
  description?: string;
  level: string;
}

export const jurisdictionService = {
  async getJurisdictions(): Promise<{ data: Jurisdiction[] }> {
    return api.get<Jurisdiction[]>('/jurisdictions/');
  },

  async getJurisdiction(id: string): Promise<{ data: Jurisdiction }> {
    return api.get<Jurisdiction>(`/jurisdictions/${id}`);
  },

  async getDistrictGeoJSON(
    jurisdictionId: string
  ): Promise<{ [districtId: string]: GeoJSON.GeoJsonObject }> {
    const res = await api.get(`/jurisdictions/${jurisdictionId}/geojson`);
    return res.data;
  },

  async createJurisdiction(data: JurisdictionCreateData): Promise<{ data: Jurisdiction }> {
    return api.post<Jurisdiction>('/jurisdictions/', data);
  },

  async updateJurisdiction(
    id: string,
    data: JurisdictionCreateData
  ): Promise<{ data: Jurisdiction }> {
    return api.put<Jurisdiction>(`/jurisdictions/${id}`, data);
  },

  async deleteJurisdiction(id: string): Promise<{ data: boolean }> {
    return api.delete<boolean>(`/jurisdictions/${id}`);
  },
};
