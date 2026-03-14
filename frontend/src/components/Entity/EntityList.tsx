import React, { useState, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Toolbar,
  Typography,
  IconButton,
  TextField,
  InputAdornment,
  Chip,
  Collapse,
  Grid,
  Button,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  SelectChangeEvent,
  Link,
  LinearProgress,
  Tooltip,
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import SearchIcon from '@mui/icons-material/Search';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import EmailIcon from '@mui/icons-material/Email';
import PhoneIcon from '@mui/icons-material/Phone';
import PublicIcon from '@mui/icons-material/Public';
import LocationOnIcon from '@mui/icons-material/LocationOn';

import { Entity, Project, EntityStatus, EntityStatusRecord, MetricDisplayConfig, UserRole } from '../../types';
import { statusService } from '../../services/status';
import { getStatusColor, getStatusLabel as getStatusLabelDefault } from '../../utils/statusColors';
import { formatMetricValue } from '../../utils/dataTransformers';
import { useAuth } from '../../contexts/AuthContext';
import ConditionalUI from '../auth/ConditionalUI';
import { compareEntities } from './entitySort';

type Order = 'asc' | 'desc';

interface EntityListProps {
  entities: Entity[];
  project: Project;
  statusRecords: EntityStatusRecord[];
  onStatusUpdated: () => void;
  getStatusLabel?: (status: EntityStatus) => string;
}

const EntityRow = ({
  entity,
  project,
  statusRecord,
  onStatusUpdated,
  getStatusLabel = getStatusLabelDefault,
  tableMetrics = [],
}: {
  entity: Entity;
  project: Project;
  statusRecord?: EntityStatusRecord;
  onStatusUpdated: () => void;
  getStatusLabel?: (status: EntityStatus) => string;
  tableMetrics?: MetricDisplayConfig[];
}) => {
  const [open, setOpen] = useState(false);
  const [status, setStatus] = useState<EntityStatus>(statusRecord?.status || EntityStatus.UNKNOWN);
  const [notes, setNotes] = useState<string>(statusRecord?.notes || '');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();
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
      if (statusRecord) {
        await statusService.updateStatusRecord(statusRecord.id, {
          entity_id: entity.id,
          project_id: project.id,
          status,
          notes,
          updated_by: user?.name || 'unknown',
        });
      } else {
        await statusService.createStatusRecord({
          entity_id: entity.id,
          project_id: project.id,
          status,
          notes,
          updated_by: user?.name || 'unknown',
        });
      }

      onStatusUpdated();
    } catch (err) {
      console.error('Error updating status:', err);
      setError('Failed to update status');
    } finally {
      setLoading(false);
    }
  };

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
              }}
            />
            <Typography variant="body1" fontWeight={500}>
              {entity.name}
            </Typography>
          </Box>
        </TableCell>

        <TableCell>{entity.title || ''}</TableCell>

        <TableCell>{entity.district_name || entity.entity_type}</TableCell>

        <TableCell align="right">
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
                    <Box display="flex" flexDirection="column" gap={1} mt={1} width="100%">
                      {entity.email && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <EmailIcon fontSize="small" color="action" />
                          <Link href={`mailto:${entity.email}`}>{entity.email}</Link>
                        </Box>
                      )}

                      {entity.phone && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <PhoneIcon fontSize="small" color="action" />
                          <Link href={`tel:${entity.phone}`}>{entity.phone}</Link>
                        </Box>
                      )}

                      {entity.website && (
                        <Box display="flex" alignItems="center" gap={1}>
                          <PublicIcon fontSize="small" color="action" />
                          <Link href={entity.website} target="_blank" rel="noopener">
                            Website
                          </Link>
                        </Box>
                      )}

                      {entity.address && (
                        <Box display="flex" alignItems="flex-start" gap={1}>
                          <LocationOnIcon fontSize="small" color="action" sx={{ mt: 0.3 }} />
                          <Typography variant="body2">{entity.address}</Typography>
                        </Box>
                      )}
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

                        <FormControl fullWidth sx={{ mb: 2 }}>
                          <InputLabel id={`status-select-label-${entity.id}`}>Status</InputLabel>
                          <Select
                            labelId={`status-select-label-${entity.id}`}
                            id={`status-select-${entity.id}`}
                            value={status}
                            label="Status"
                            onChange={handleStatusChange}
                            disabled={loading}
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
                            <MenuItem value={EntityStatus.SOLID_APPROVAL}>
                              <Box display="flex" alignItems="center" gap={1}>
                                <Box
                                  width={12}
                                  height={12}
                                  borderRadius="50%"
                                  bgcolor={getStatusColor(EntityStatus.SOLID_APPROVAL)}
                                />
                                Solid Approval
                              </Box>
                            </MenuItem>
                            <MenuItem value={EntityStatus.LEANING_APPROVAL}>
                              <Box display="flex" alignItems="center" gap={1}>
                                <Box
                                  width={12}
                                  height={12}
                                  borderRadius="50%"
                                  bgcolor={getStatusColor(EntityStatus.LEANING_APPROVAL)}
                                />
                                Leaning Approval
                              </Box>
                            </MenuItem>
                            <MenuItem value={EntityStatus.NEUTRAL}>
                              <Box display="flex" alignItems="center" gap={1}>
                                <Box
                                  width={12}
                                  height={12}
                                  borderRadius="50%"
                                  bgcolor={getStatusColor(EntityStatus.NEUTRAL)}
                                />
                                Neutral
                              </Box>
                            </MenuItem>
                            <MenuItem value={EntityStatus.LEANING_DISAPPROVAL}>
                              <Box display="flex" alignItems="center" gap={1}>
                                <Box
                                  width={12}
                                  height={12}
                                  borderRadius="50%"
                                  bgcolor={getStatusColor(EntityStatus.LEANING_DISAPPROVAL)}
                                />
                                Leaning Disapproval
                              </Box>
                            </MenuItem>
                            <MenuItem value={EntityStatus.SOLID_DISAPPROVAL}>
                              <Box display="flex" alignItems="center" gap={1}>
                                <Box
                                  width={12}
                                  height={12}
                                  borderRadius="50%"
                                  bgcolor={getStatusColor(EntityStatus.SOLID_DISAPPROVAL)}
                                />
                                Solid Disapproval
                              </Box>
                            </MenuItem>
                            <MenuItem value={EntityStatus.UNKNOWN}>
                              <Box display="flex" alignItems="center" gap={1}>
                                <Box
                                  width={12}
                                  height={12}
                                  borderRadius="50%"
                                  bgcolor={getStatusColor(EntityStatus.UNKNOWN)}
                                />
                                Unknown
                              </Box>
                            </MenuItem>
                          </Select>
                        </FormControl>

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

const EntityList: React.FC<EntityListProps> = ({
  entities,
  project,
  statusRecords,
  onStatusUpdated,
  getStatusLabel = getStatusLabelDefault,
}) => {
  const tableMetrics = useMemo(
    () => project.dashboard_config?.metrics?.filter(m => m.show_in_table !== false) ?? [],
    [project.dashboard_config?.metrics]
  );

  // State for filtering and sorting
  const [order, setOrder] = useState<Order>('asc');
  const [orderBy, setOrderBy] = useState<keyof Entity | 'status' | string>('name');
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');

  const statusRecordsMap = useMemo(() => {
    const map: Record<string, EntityStatusRecord> = {};
    for (const sr of statusRecords) {
      if (sr.project_id === project.id) {
        map[sr.entity_id] = sr;
      }
    }
    return map;
  }, [statusRecords, project.id]);

  // Sort entities based on orderBy and order
  const sortedEntities = useMemo(() => {
    const metricKeys = tableMetrics.map(m => m.key);
    return [...entities].sort((a, b) =>
      compareEntities(a, b, orderBy, order, statusRecordsMap, metricKeys)
    );
  }, [entities, order, orderBy, statusRecordsMap, tableMetrics]);

  // Filter entities based on search term and filter settings
  const filteredEntities = useMemo(() => {
    return sortedEntities.filter(entity => {
      // Filter by search term
      const matchesSearch =
        searchTerm === '' ||
        entity.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (entity.title && entity.title.toLowerCase().includes(searchTerm.toLowerCase())) ||
        (entity.district_name &&
          entity.district_name.toLowerCase().includes(searchTerm.toLowerCase()));

      // Filter by status
      if (filterStatus !== 'all') {
        const statusRecord = statusRecords.find(
          sr => sr.entity_id === entity.id && sr.project_id === project.id
        );
        const entityStatus = statusRecord?.status || EntityStatus.UNKNOWN;
        if (entityStatus !== filterStatus) {
          return false;
        }
      }

      return matchesSearch;
    });
  }, [sortedEntities, searchTerm, filterStatus, statusRecords, project.id]);

  const handleRequestSort = (property: keyof Entity | 'status' | string) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  return (
    <Box sx={{ width: '100%' }}>
      <Paper sx={{ width: '100%', mb: 2, borderRadius: 2, overflow: 'hidden' }}>
        <Toolbar
          sx={{
            pl: { sm: 2 },
            pr: { xs: 1, sm: 1 },
            flexDirection: { xs: 'column', sm: 'row' }, // Stack vertically on mobile
            alignItems: { xs: 'flex-start', sm: 'center' },
            '& > :first-of-type': {
              mb: { xs: 1, sm: 0 }, // Add margin below title on mobile
            },
          }}
        >
          <Typography sx={{ flex: '1 1 100%' }} variant="h6" id="tableTitle" component="div">
            Representatives
          </Typography>

          <Box
            display="flex"
            alignItems="center"
            gap={2}
            sx={{
              width: { xs: '100%', sm: 'auto' },
              flexWrap: { xs: 'wrap', sm: 'nowrap' },
              justifyContent: { xs: 'space-between', sm: 'flex-end' },
            }}
          >
            <FormControl
              variant="outlined"
              size="small"
              sx={{ width: { xs: '120px', sm: '150px' } }}
            >
              <InputLabel id="status-filter-label">Status</InputLabel>
              <Select
                labelId="status-filter-label"
                id="status-filter"
                value={filterStatus}
                onChange={e => setFilterStatus(e.target.value)}
                label="Status"
              >
                <MenuItem value="all">All Statuses</MenuItem>
                <MenuItem value={EntityStatus.SOLID_APPROVAL}>
                  {getStatusLabel(EntityStatus.SOLID_APPROVAL)}
                </MenuItem>
                <MenuItem value={EntityStatus.LEANING_APPROVAL}>
                  {getStatusLabel(EntityStatus.LEANING_APPROVAL)}
                </MenuItem>
                <MenuItem value={EntityStatus.NEUTRAL}>
                  {getStatusLabel(EntityStatus.NEUTRAL)}
                </MenuItem>
                <MenuItem value={EntityStatus.LEANING_DISAPPROVAL}>
                  {getStatusLabel(EntityStatus.LEANING_DISAPPROVAL)}
                </MenuItem>
                <MenuItem value={EntityStatus.SOLID_DISAPPROVAL}>
                  {getStatusLabel(EntityStatus.SOLID_DISAPPROVAL)}
                </MenuItem>
                <MenuItem value={EntityStatus.UNKNOWN}>
                  {getStatusLabel(EntityStatus.UNKNOWN)}
                </MenuItem>
              </Select>
            </FormControl>

            <TextField
              size="small"
              variant="outlined"
              placeholder="Search entities..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              sx={{
                width: { xs: '100%', sm: '220px' },
                flexGrow: { xs: 1, sm: 0 },
                mt: { xs: 1, sm: 0 },
              }}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Box>
        </Toolbar>
        <TableContainer
          sx={{
            overflowX: 'auto', // Allows horizontal scrolling on mobile if needed
            '& .MuiTableCell-root': {
              // Make table cells more compact on mobile
              padding: { xs: '8px 6px', sm: '16px' },
              whiteSpace: { xs: 'nowrap', sm: 'normal' },
            },
          }}
        >
          <Table aria-labelledby="tableTitle" size="medium">
            <TableHead>
              <TableRow>
                <TableCell padding="checkbox" />
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'name'}
                    direction={orderBy === 'name' ? order : 'asc'}
                    onClick={() => handleRequestSort('name')}
                  >
                    Name
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'title'}
                    direction={orderBy === 'title' ? order : 'asc'}
                    onClick={() => handleRequestSort('title')}
                  >
                    Title
                  </TableSortLabel>
                </TableCell>
                <TableCell>
                  <TableSortLabel
                    active={orderBy === 'district_name'}
                    direction={orderBy === 'district_name' ? order : 'asc'}
                    onClick={() => handleRequestSort('district_name')}
                  >
                    District
                  </TableSortLabel>
                </TableCell>
                <TableCell align="right">
                  <TableSortLabel
                    active={orderBy === 'status'}
                    direction={orderBy === 'status' ? order : 'asc'}
                    onClick={() => handleRequestSort('status')}
                  >
                    Status
                  </TableSortLabel>
                </TableCell>
                {tableMetrics.map(metric => (
                  <TableCell key={metric.key} align="right">
                    <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
                      <TableSortLabel
                        active={orderBy === metric.key}
                        direction={orderBy === metric.key ? order : 'asc'}
                        onClick={() => handleRequestSort(metric.key)}
                      >
                        {metric.label}
                      </TableSortLabel>
                      {metric.description && (
                        <Tooltip title={metric.description} arrow>
                          <InfoOutlinedIcon sx={{ fontSize: 14, color: 'text.secondary', cursor: 'help' }} />
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                ))}
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredEntities.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6 + tableMetrics.length} align="center" sx={{ py: 3 }}>
                    <Typography variant="body1" color="text.secondary">
                      No entities found matching your criteria
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                filteredEntities.map(entity => (
                  <EntityRow
                    key={entity.id}
                    entity={entity}
                    project={project}
                    statusRecord={statusRecords.find(
                      sr => sr.entity_id === entity.id && sr.project_id === project.id
                    )}
                    onStatusUpdated={onStatusUpdated}
                    getStatusLabel={getStatusLabel}
                    tableMetrics={tableMetrics}
                  />
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default EntityList;
