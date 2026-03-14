import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { EntityStatus, EntityStatusRecord } from '../types';

vi.mock('../services/status', () => ({
  statusService: {
    createStatusRecord: vi.fn().mockResolvedValue({ data: {} }),
    updateStatusRecord: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

vi.mock('../contexts/AuthContext', () => ({
  useAuth: () => ({ user: { name: 'editor-user' } }),
}));

import { useEntityStatusForm } from './useEntityStatusForm';
import { statusService } from '../services/status';

const entity = {
  id: 'ent-1',
  name: 'Jane Doe',
  entity_type: 'alderman',
  jurisdiction_id: 'jur-1',
};

const existingRecord: EntityStatusRecord = {
  id: 'sr-1',
  entity_id: 'ent-1',
  project_id: 'proj-1',
  status: EntityStatus.LEANING_APPROVAL,
  notes: 'Existing note',
  updated_at: '2024-01-01T00:00:00Z',
  updated_by: 'admin',
};

describe('useEntityStatusForm — initial state', () => {
  it('initialises status and notes from existingRecord', () => {
    const { result } = renderHook(() =>
      useEntityStatusForm({
        entity,
        projectId: 'proj-1',
        existingRecord,
        onUpdated: vi.fn(),
      })
    );
    expect(result.current.status).toBe(EntityStatus.LEANING_APPROVAL);
    expect(result.current.notes).toBe('Existing note');
  });

  it('defaults to UNKNOWN status and empty notes when no existingRecord', () => {
    const { result } = renderHook(() =>
      useEntityStatusForm({ entity, projectId: 'proj-1', onUpdated: vi.fn() })
    );
    expect(result.current.status).toBe(EntityStatus.UNKNOWN);
    expect(result.current.notes).toBe('');
  });
});

describe('useEntityStatusForm — handleSubmit', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('calls updateStatusRecord (not create) when existingRecord is present', async () => {
    const onUpdated = vi.fn();
    const { result } = renderHook(() =>
      useEntityStatusForm({ entity, projectId: 'proj-1', existingRecord, onUpdated })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(statusService.updateStatusRecord).toHaveBeenCalledOnce();
    expect(statusService.updateStatusRecord).toHaveBeenCalledWith(
      'sr-1',
      expect.objectContaining({ entity_id: 'ent-1', project_id: 'proj-1' })
    );
    expect(statusService.createStatusRecord).not.toHaveBeenCalled();
  });

  it('calls createStatusRecord (not update) when no existingRecord', async () => {
    const onUpdated = vi.fn();
    const { result } = renderHook(() =>
      useEntityStatusForm({ entity, projectId: 'proj-1', onUpdated })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(statusService.createStatusRecord).toHaveBeenCalledOnce();
    expect(statusService.createStatusRecord).toHaveBeenCalledWith(
      expect.objectContaining({ entity_id: 'ent-1', project_id: 'proj-1' })
    );
    expect(statusService.updateStatusRecord).not.toHaveBeenCalled();
  });

  it('calls onUpdated after a successful submit', async () => {
    const onUpdated = vi.fn();
    const { result } = renderHook(() =>
      useEntityStatusForm({ entity, projectId: 'proj-1', existingRecord, onUpdated })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(onUpdated).toHaveBeenCalledOnce();
  });

  it('sets error and does not call onUpdated when the service throws', async () => {
    vi.mocked(statusService.updateStatusRecord).mockRejectedValueOnce(new Error('Network error'));
    const onUpdated = vi.fn();
    const { result } = renderHook(() =>
      useEntityStatusForm({ entity, projectId: 'proj-1', existingRecord, onUpdated })
    );

    await act(async () => {
      await result.current.handleSubmit();
    });

    expect(result.current.error).toBe('Failed to update status');
    expect(onUpdated).not.toHaveBeenCalled();
  });

  it('clears a previous error on a successful retry', async () => {
    vi.mocked(statusService.updateStatusRecord)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({ data: {} as EntityStatusRecord });

    const { result } = renderHook(() =>
      useEntityStatusForm({ entity, projectId: 'proj-1', existingRecord, onUpdated: vi.fn() })
    );

    await act(async () => { await result.current.handleSubmit(); });
    expect(result.current.error).toBe('Failed to update status');

    await act(async () => { await result.current.handleSubmit(); });
    expect(result.current.error).toBeNull();
  });
});
