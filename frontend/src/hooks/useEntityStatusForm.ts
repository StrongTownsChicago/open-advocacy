import { useState } from 'react';
import { SelectChangeEvent } from '@mui/material';
import { Entity, EntityStatus, EntityStatusRecord } from '../types';
import { statusService } from '../services/status';
import { useAuth } from '../contexts/AuthContext';

interface UseEntityStatusFormProps {
  entity: Entity;
  projectId: string;
  existingRecord?: EntityStatusRecord;
  onUpdated: () => void;
}

interface UseEntityStatusFormReturn {
  status: EntityStatus;
  notes: string;
  loading: boolean;
  error: string | null;
  handleStatusChange: (event: SelectChangeEvent<EntityStatus>) => void;
  handleNotesChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
  handleSubmit: () => Promise<void>;
}

export const useEntityStatusForm = ({
  entity,
  projectId,
  existingRecord,
  onUpdated,
}: UseEntityStatusFormProps): UseEntityStatusFormReturn => {
  const [status, setStatus] = useState<EntityStatus>(
    existingRecord?.status || EntityStatus.UNKNOWN
  );
  const [notes, setNotes] = useState<string>(existingRecord?.notes || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const { user } = useAuth();

  const handleStatusChange = (event: SelectChangeEvent<EntityStatus>) => {
    setStatus(event.target.value as EntityStatus);
  };

  const handleNotesChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setNotes(event.target.value);
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      if (existingRecord) {
        await statusService.updateStatusRecord(existingRecord.id, {
          entity_id: entity.id,
          project_id: projectId,
          status,
          notes,
          updated_by: user?.name || 'unknown',
        });
      } else {
        await statusService.createStatusRecord({
          entity_id: entity.id,
          project_id: projectId,
          status,
          notes,
          updated_by: user?.name || 'unknown',
        });
      }

      onUpdated();
    } catch (err) {
      console.error('Error updating status:', err);
      setError('Failed to update status');
    } finally {
      setLoading(false);
    }
  };

  return {
    status,
    notes,
    loading,
    error,
    handleStatusChange,
    handleNotesChange,
    handleSubmit,
  };
};
