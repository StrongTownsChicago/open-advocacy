import { describe, it, expect, vi, beforeEach } from 'vitest';
import { ProjectStatus, EntityStatus } from '../types';

// Mock the api module before importing the service
vi.mock('./api', () => {
  const mockApi = {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: true }),
    defaults: { baseURL: 'https://test.com/api' },
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  };
  return { default: mockApi };
});

import { projectService } from './projects';
import api from './api';

describe('projectService.getProjects', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls /projects/ with no query params when no filters provided', async () => {
    await projectService.getProjects();
    expect(api.get).toHaveBeenCalledWith('/projects/');
  });

  it('appends status filter to query string', async () => {
    await projectService.getProjects({ status: ProjectStatus.ACTIVE });
    expect(api.get).toHaveBeenCalledWith('/projects/?status=active');
  });

  it('appends multiple filters to query string', async () => {
    await projectService.getProjects({
      status: ProjectStatus.ACTIVE,
      group_id: 'grp-123',
      skip: 10,
      limit: 25,
    });
    const calledUrl = (api.get as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(calledUrl).toContain('status=active');
    expect(calledUrl).toContain('group_id=grp-123');
    expect(calledUrl).toContain('skip=10');
    expect(calledUrl).toContain('limit=25');
  });

  it('omits undefined optional params', async () => {
    await projectService.getProjects({ status: ProjectStatus.DRAFT });
    const calledUrl = (api.get as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(calledUrl).not.toContain('group_id');
    expect(calledUrl).not.toContain('skip');
    expect(calledUrl).not.toContain('limit');
  });
});

describe('projectService.createProject', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('sets default preferred_status to SOLID_APPROVAL when not provided', async () => {
    await projectService.createProject({
      title: 'Test Project',
      jurisdiction_id: 'jur-1',
      group_id: 'grp-1',
    });
    const calledData = (api.post as ReturnType<typeof vi.fn>).mock.calls[0][1];
    expect(calledData.preferred_status).toBe(EntityStatus.SOLID_APPROVAL);
  });

  it('preserves explicit preferred_status', async () => {
    await projectService.createProject({
      title: 'Test Project',
      preferred_status: EntityStatus.NEUTRAL,
    });
    const calledData = (api.post as ReturnType<typeof vi.fn>).mock.calls[0][1];
    expect(calledData.preferred_status).toBe(EntityStatus.NEUTRAL);
  });
});

describe('projectService.getProjectByName', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('encodes project name in URL', async () => {
    await projectService.getProjectByName('ADU Opt-In Project');
    expect(api.get).toHaveBeenCalledWith('/projects/by-name/ADU%20Opt-In%20Project');
  });
});

describe('projectService.getProjectBySlug', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls correct endpoint with slug', async () => {
    await projectService.getProjectBySlug('my-slug');
    expect(api.get).toHaveBeenCalledWith('/projects/slug/my-slug');
  });

  it('URL-encodes the slug', async () => {
    await projectService.getProjectBySlug('my slug/with special');
    expect(api.get).toHaveBeenCalledWith('/projects/slug/my%20slug%2Fwith%20special');
  });
});
