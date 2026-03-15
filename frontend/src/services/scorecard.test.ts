import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./api', () => {
  const mockApi = {
    get: vi.fn().mockResolvedValue({ data: {} }),
    post: vi.fn().mockResolvedValue({ data: { updated: 0, errors: 0 } }),
    defaults: { baseURL: '/api' },
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  };
  return { default: mockApi };
});

import { scorecardService } from './scorecard';
import api from './api';

describe('scorecardService.refreshScorecardData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls POST /admin/scorecard/refresh', async () => {
    await scorecardService.refreshScorecardData();
    expect(api.post).toHaveBeenCalledWith('/admin/scorecard/refresh');
  });

  it('returns the response data from the API', async () => {
    vi.mocked(api.post).mockResolvedValueOnce({ data: { updated: 5, errors: 1 } });
    const result = await scorecardService.refreshScorecardData();
    expect(result).toEqual({ data: { updated: 5, errors: 1 } });
  });
});
