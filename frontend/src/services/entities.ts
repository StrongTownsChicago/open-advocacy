import api from './api';
import { Entity } from '../types';

export const entityService = {
  async getEntitiesByJurisdictions(jurisdictionId: string): Promise<{ data: Entity[] }> {
    const params = new URLSearchParams({ jurisdiction_id: jurisdictionId });
    return api.get<Entity[]>(`/entities/?${params.toString()}`);
  },

  async findByAddress(address: string): Promise<{ data: Entity[] }> {
    return api.post<Entity[]>('/entities/address_lookup', { address });
  },

  async getEntity(id: string): Promise<{ data: Entity }> {
    return api.get<Entity>(`/entities/${id}`);
  },
};
