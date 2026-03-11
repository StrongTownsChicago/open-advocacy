import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('./api', () => {
  const mockApi = {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    defaults: { baseURL: '/api' },
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  };
  return { default: mockApi };
});

import { importsService } from './imports';
import api from './api';

describe('importsService.getLocations', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls GET /imports/locations', async () => {
    await importsService.getLocations();
    expect(api.get).toHaveBeenCalledWith('/imports/locations');
  });
});

describe('importsService.triggerImport', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls POST /imports/locations/{key}', async () => {
    await importsService.triggerImport('chicago');
    expect(api.post).toHaveBeenCalledWith('/imports/locations/chicago');
  });

  it('URL-encodes the location key', async () => {
    await importsService.triggerImport('my location');
    expect(api.post).toHaveBeenCalledWith('/imports/locations/my%20location');
  });
});
