import { describe, it, expect, vi, beforeEach } from 'vitest';
import { EntityStatus } from '../types';

vi.mock('./api', () => ({
  default: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: true }),
    defaults: { baseURL: '/api' },
    interceptors: { request: { use: vi.fn() }, response: { use: vi.fn() } },
  },
}));

import { statusService } from './status';
import api from './api';

describe('statusService.getStatusRecords', () => {
  beforeEach(() => vi.clearAllMocks());

  it('calls /status/ with no params when called with no arguments', async () => {
    await statusService.getStatusRecords();
    expect(api.get).toHaveBeenCalledWith('/status/');
  });

  it('appends project_id param when provided', async () => {
    await statusService.getStatusRecords('proj-1');
    expect(api.get).toHaveBeenCalledWith('/status/?project_id=proj-1');
  });

  it('appends entity_id param when provided', async () => {
    await statusService.getStatusRecords(undefined, 'ent-1');
    expect(api.get).toHaveBeenCalledWith('/status/?entity_id=ent-1');
  });

  it('appends both params when both are provided', async () => {
    await statusService.getStatusRecords('proj-1', 'ent-1');
    const url = (api.get as ReturnType<typeof vi.fn>).mock.calls[0][0] as string;
    expect(url).toContain('project_id=proj-1');
    expect(url).toContain('entity_id=ent-1');
  });
});

describe('statusService.createStatusRecord', () => {
  beforeEach(() => vi.clearAllMocks());

  it('posts to /status/ with the provided fields', async () => {
    await statusService.createStatusRecord({
      entity_id: 'ent-1',
      project_id: 'proj-1',
      status: EntityStatus.SOLID_APPROVAL,
      updated_by: 'admin',
    });
    const body = (api.post as ReturnType<typeof vi.fn>).mock.calls[0][1];
    expect(body.entity_id).toBe('ent-1');
    expect(body.status).toBe(EntityStatus.SOLID_APPROVAL);
  });

  it('includes updated_at timestamp', async () => {
    await statusService.createStatusRecord({
      entity_id: 'ent-1',
      project_id: 'proj-1',
      status: EntityStatus.NEUTRAL,
      updated_by: 'admin',
    });
    const body = (api.post as ReturnType<typeof vi.fn>).mock.calls[0][1];
    expect(body.updated_at).toBeDefined();
    expect(() => new Date(body.updated_at)).not.toThrow();
  });
});

describe('statusService.updateStatusRecord', () => {
  beforeEach(() => vi.clearAllMocks());

  it('puts to /status/:id with the updated fields', async () => {
    await statusService.updateStatusRecord('sr-1', {
      status: EntityStatus.LEANING_DISAPPROVAL,
      notes: 'Changed mind',
      updated_by: 'editor',
    });
    expect(api.put).toHaveBeenCalledWith(
      '/status/sr-1',
      expect.objectContaining({ status: EntityStatus.LEANING_DISAPPROVAL, notes: 'Changed mind' })
    );
  });
});
