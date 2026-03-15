import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  TableCell,
  TableRow,
  Typography,
  IconButton,
  TextField,
  Chip,
  Collapse,
  Grid,
  Button,
  Divider,
  Paper,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';

import { Entity, Project, EntityStatus, EntityStatusRecord, MetricDisplayConfig, UserRole } from '../../types';
import { getStatusColor, makeStatusLabelFn } from '../../utils/statusColors';
import { formatMetricValue } from '../../utils/dataTransformers';
import ConditionalUI from '../auth/ConditionalUI';
import EntityContactInfo from './EntityContactInfo';
import StatusSelectMenu from './StatusSelectMenu';
import { useEntityStatusForm } from '../../hooks/useEntityStatusForm';

export interface EntityRowProps {
  entity: Entity;
  project: Project;
  statusRecord?: EntityStatusRecord;
  onStatusUpdated: () => void;
  tableMetrics?: MetricDisplayConfig[];
}

const EntityRow: React.FC<EntityRowProps> = ({
  entity,
  project,
  statusRecord,
  onStatusUpdated,
  tableMetrics = [],
}) => {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const getStatusLabel = makeStatusLabelFn(project.dashboard_config?.status_labels);

  const { status, notes, loading, error, handleStatusChange, handleNotesChange, handleSubmit } =
    useEntityStatusForm({
      entity,
      projectId: project.id,
      existingRecord: statusRecord,
      onUpdated: onStatusUpdated,
    });

  const CurrentStatusInfo = () =>
    statusRecord ? (
      <Box width="100%">
        <Typography variant="subtitle2" gutterBottom>
          Current Status
        </Typography>
        <Box
          p={2}
          sx={{
            width: '100%',
            bgcolor: 'rgba(0,0,0,0.02)',
            borderRadius: 1,
            border: `1px solid ${getStatusColor(statusRecord.status)}`,
          }}
        >
          <Typography fontWeight="600" color={getStatusColor(statusRecord.status)}>
            {getStatusLabel(statusRecord.status)}
          </Typography>

          {statusRecord.notes && (
            <>
              <Divider sx={{ my: 1.5 }} />
              <Typography variant="body2">{statusRecord.notes}</Typography>
            </>
          )}

          <Typography variant="caption" color="text.secondary" display="block" mt={1}>
            Last updated: {new Date(statusRecord.updated_at).toLocaleString()}
          </Typography>
        </Box>
      </Box>
    ) : null;

  return (
    <>
      <TableRow
        hover
        sx={{
          '& > *': { borderBottom: 'unset' },
          cursor: 'pointer',
          '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' },
        }}
        onClick={() => setOpen(!open)}
      >
        <TableCell padding="checkbox">
          <IconButton
            aria-label="expand row"
            size="small"
            onClick={e => {
              e.stopPropagation();
              setOpen(!open);
            }}
          >
            {open ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
          </IconButton>
        </TableCell>

        <TableCell component="th" scope="row">
          <Box display="flex" alignItems="center" gap={1}>
            <Chip
              size="small"
              sx={{
                bgcolor: getStatusColor(statusRecord?.status ?? EntityStatus.UNKNOWN),
                width: 10,
                height: 10,
                borderRadius: '50%',
                flexShrink: 0,
              }}
            />
            <Box>
              <Typography variant="body1" fontWeight={500}>
                {entity.name}
              </Typography>
              {(entity.district_name || entity.entity_type) && (
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ display: { xs: 'block', sm: 'none' } }}
                >
                  {entity.district_name || entity.entity_type}
                </Typography>
              )}
            </Box>
          </Box>
        </TableCell>

        <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{entity.title || ''}</TableCell>

        <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>{entity.district_name || entity.entity_type}</TableCell>

        <TableCell>
          <Tooltip
            title={statusRecord?.notes ?? ''}
            arrow
            disableHoverListener={!statusRecord?.notes}
            disableFocusListener={!statusRecord?.notes}
            disableTouchListener={!statusRecord?.notes}
          >
            <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
              <Chip
                label={getStatusLabel(statusRecord?.status ?? EntityStatus.UNKNOWN)}
                size="small"
                sx={{
                  bgcolor: getStatusColor(statusRecord?.status ?? EntityStatus.UNKNOWN),
                  color: '#fff',
                  fontWeight: 500,
                  cursor: statusRecord?.notes ? 'help' : 'default',
                }}
              />
              {statusRecord?.notes && (
                <InfoOutlinedIcon sx={{ fontSize: 14, color: 'text.disabled', pointerEvents: 'none' }} />
              )}
            </Box>
          </Tooltip>
        </TableCell>
        {tableMetrics.map(metric => {
          const rawValue = statusRecord?.record_metadata?.[metric.key];
          const numericValue = typeof rawValue === 'number' ? rawValue : parseFloat(String(rawValue));
          return (
            <TableCell key={metric.key} align="right">
              {formatMetricValue(rawValue, metric.format ?? 'text')}
              {metric.format === 'percentage' && !isNaN(numericValue) && (
                <LinearProgress
                  variant="determinate"
                  value={Math.min(numericValue, 100)}
                  sx={{ height: 4, borderRadius: 1, mt: 0.5 }}
                />
              )}
            </TableCell>
          );
        })}
      </TableRow>

      <TableRow>
        <TableCell style={{ paddingBottom: 0, paddingTop: 0 }} colSpan={6 + tableMetrics.length}>
          <Collapse in={open} timeout="auto" unmountOnExit sx={{ width: '100%' }}>
            <Box sx={{ margin: 2, width: '100%' }}>
              <Grid container spacing={2} sx={{ width: '100%' }}>
                {/* Contact Information - Always shown */}
                <Grid size={{ xs: 12, md: 12 }} sx={{ width: '100%' }}>
                  <Paper
                    elevation={0}
                    sx={{
                      p: { xs: 1.5, sm: 2 },
                      bgcolor: 'rgba(0,0,0,0.02)',
                      borderRadius: 1,
                      width: '100%',
                    }}
                  >
                    <Typography variant="subtitle2" gutterBottom>
                      Contact Information
                    </Typography>
                    <Box mt={1} width="100%">
                      <EntityContactInfo entity={entity} />
                    </Box>
                  </Paper>
                  <Box mt={1} width="100%">
                    <Button
                      variant="outlined"
                      size="small"
                      onClick={() => navigate(`/representatives/${entity.id}`)}
                      sx={{ mr: 1 }}
                    >
                      View Representative Details
                    </Button>
                  </Box>
                </Grid>

                {/* Status Controls - Conditionally shown based on auth */}
                <Grid size={{ xs: 12, md: 12 }} sx={{ width: '100%' }}>
                  <Box display="flex" flexDirection="column" gap={2} width="100%">
                    {/* Status update form - only for authenticated users */}
                    <ConditionalUI
                      requireAuth={true}
                      requiredRoles={[UserRole.EDITOR, UserRole.GROUP_ADMIN, UserRole.SUPER_ADMIN]}
                    >
                      <Box sx={{ width: '100%', overflowX: 'hidden' }}>
                        <Typography variant="subtitle2" gutterBottom>
                          Update Status
                        </Typography>

                        <StatusSelectMenu
                          entityId={entity.id}
                          value={status}
                          onChange={handleStatusChange}
                          disabled={loading}
                          statusLabels={project.dashboard_config?.status_labels}
                        />

                        <TextField
                          fullWidth
                          label="Notes"
                          multiline
                          rows={3}
                          value={notes}
                          onChange={handleNotesChange}
                          disabled={loading}
                          sx={{ mb: 2 }}
                        />

                        <Box sx={{ display: 'flex', flexDirection: 'column', width: '100%' }}>
                          <Button
                            variant="contained"
                            color="primary"
                            onClick={e => {
                              e.stopPropagation();
                              handleSubmit();
                            }}
                            disabled={loading}
                            sx={{ minWidth: 120, alignSelf: 'flex-start' }}
                          >
                            {loading ? 'Saving...' : statusRecord ? 'Update' : 'Save'}
                          </Button>

                          {error && (
                            <Typography color="error" sx={{ mt: 1 }}>
                              {error}
                            </Typography>
                          )}
                        </Box>
                      </Box>
                    </ConditionalUI>

                    {/* Status display - always shown if there's a status */}
                    {statusRecord && <CurrentStatusInfo />}
                  </Box>
                </Grid>
              </Grid>
            </Box>
          </Collapse>
        </TableCell>
      </TableRow>
    </>
  );
};

export default EntityRow;
