import api from './api';
import { ScorecardResponse } from '../types';

export interface ScorecardRefreshResult {
  updated: number;
  errors: number;
}

export const scorecardService = {
  getScorecard: (groupSlug: string) =>
    api.get<ScorecardResponse>(`/scorecard/${groupSlug}`),

  async refreshScorecardData(): Promise<{ data: ScorecardRefreshResult }> {
    return api.post<ScorecardRefreshResult>('/admin/scorecard/refresh');
  },
};
