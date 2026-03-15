import React, { useState, useMemo } from 'react';
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
  TextField,
  InputAdornment,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip,
} from '@mui/material';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import SearchIcon from '@mui/icons-material/Search';

import { Entity, Project, EntityStatus, EntityStatusRecord } from '../../types';
import { makeStatusLabelFn } from '../../utils/statusColors';
import { compareEntities } from './entitySort';
import EntityRow from './EntityRow';

type Order = 'asc' | 'desc';

interface EntityListProps {
  entities: Entity[];
  project: Project;
  statusRecords: EntityStatusRecord[];
  onStatusUpdated: () => void;
}

const EntityList: React.FC<EntityListProps> = ({
  entities,
  project,
  statusRecords,
  onStatusUpdated,
}) => {
  const getStatusLabel = makeStatusLabelFn(project.dashboard_config?.status_labels);

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
            pl: { sm: 2.5 },
            pr: { xs: 1.5, sm: 2 },
            py: { xs: 1.5, sm: 1.5 },
            minHeight: { xs: 'auto', sm: '56px' },
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: { xs: 'flex-start', sm: 'center' },
            '& > :first-of-type': {
              mb: { xs: 1, sm: 0 },
            },
          }}
        >
          <Typography
            sx={{
              flex: '1 1 100%',
              fontFamily: '"Fraunces", Georgia, serif',
              fontWeight: 600,
              fontSize: '1.1rem',
            }}
            variant="h6"
            id="tableTitle"
            component="div"
          >
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
            overflowX: 'auto',
            '& .MuiTableCell-root': {
              padding: { xs: '8px 6px', sm: '16px' },
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
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  <TableSortLabel
                    active={orderBy === 'title'}
                    direction={orderBy === 'title' ? order : 'asc'}
                    onClick={() => handleRequestSort('title')}
                  >
                    Title
                  </TableSortLabel>
                </TableCell>
                <TableCell sx={{ display: { xs: 'none', sm: 'table-cell' } }}>
                  <TableSortLabel
                    active={orderBy === 'district_name'}
                    direction={orderBy === 'district_name' ? order : 'asc'}
                    onClick={() => handleRequestSort('district_name')}
                  >
                    District
                  </TableSortLabel>
                </TableCell>
                <TableCell>
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
