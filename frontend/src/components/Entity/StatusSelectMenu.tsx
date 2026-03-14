import React from 'react';
import { Box, FormControl, InputLabel, Select, MenuItem, SelectChangeEvent } from '@mui/material';
import { EntityStatus } from '../../types';
import { getStatusColor, makeStatusLabelFn } from '../../utils/statusColors';

interface StatusSelectMenuProps {
  entityId: string;
  value: EntityStatus;
  onChange: (event: SelectChangeEvent<EntityStatus>) => void;
  disabled?: boolean;
  statusLabels?: Record<string, string>;
}

const StatusSelectMenu: React.FC<StatusSelectMenuProps> = ({
  entityId,
  value,
  onChange,
  disabled = false,
  statusLabels,
}) => {
  const getStatusLabel = makeStatusLabelFn(statusLabels);
  return (
    <FormControl fullWidth sx={{ mb: 2 }}>
      <InputLabel id={`status-select-label-${entityId}`}>Status</InputLabel>
      <Select
        labelId={`status-select-label-${entityId}`}
        id={`status-select-${entityId}`}
        value={value}
        label="Status"
        onChange={onChange}
        disabled={disabled}
        fullWidth
        MenuProps={{
          PaperProps: {
            sx: {
              [`@media (max-width:600px)`]: {
                left: '0 !important',
                maxWidth: '280px !important',
              },
            },
          },
          anchorOrigin: {
            vertical: 'bottom',
            horizontal: 'left',
          },
          transformOrigin: {
            vertical: 'top',
            horizontal: 'left',
          },
        }}
      >
        {[
          EntityStatus.SOLID_APPROVAL,
          EntityStatus.LEANING_APPROVAL,
          EntityStatus.NEUTRAL,
          EntityStatus.LEANING_DISAPPROVAL,
          EntityStatus.SOLID_DISAPPROVAL,
          EntityStatus.UNKNOWN,
        ].map(s => (
          <MenuItem key={s} value={s}>
            <Box display="flex" alignItems="center" gap={1}>
              <Box width={12} height={12} borderRadius="50%" bgcolor={getStatusColor(s)} />
              {getStatusLabel(s)}
            </Box>
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
};

export default StatusSelectMenu;
