import api from './api';
import { ScorecardResponse } from '../types';

export const scorecardService = {
  getScorecard: (groupSlug: string) =>
    api.get<ScorecardResponse>(`/scorecard/${groupSlug}`),
};
