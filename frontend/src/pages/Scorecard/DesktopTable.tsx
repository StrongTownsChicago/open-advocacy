import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import OpenInNewIcon from '@mui/icons-material/OpenInNew';
import {
  Box,
  Chip,
  Link as MuiLink,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Tooltip,
  Typography,
} from '@mui/material';
import { ScorecardEntityRow, ScorecardResponse } from '../../types';
import { getStatusColor } from '../../utils/statusColors';

type SortDirection = 'asc' | 'desc';

interface DesktopTableProps {
  rows: ScorecardEntityRow[];
  data: ScorecardResponse;
  sortField: string;
  sortDirection: SortDirection;
  onSort: (field: string) => void;
}

const DesktopTable: React.FC<DesktopTableProps> = ({ rows, data, sortField, sortDirection, onSort }) => (
  <TableContainer
    sx={{ maxHeight: '75vh', border: '1px solid', borderColor: 'divider', borderRadius: 1 }}
  >
    <Table stickyHeader size="small">
      <TableHead>
        <TableRow>
          <TableCell sx={{ fontWeight: 700, minWidth: 80 }}>
            <TableSortLabel
              active={sortField === 'ward'}
              direction={sortField === 'ward' ? sortDirection : 'asc'}
              onClick={() => onSort('ward')}
            >
              Ward
            </TableSortLabel>
          </TableCell>
          <TableCell sx={{ fontWeight: 700, minWidth: 160 }}>
            <TableSortLabel
              active={sortField === 'name'}
              direction={sortField === 'name' ? sortDirection : 'asc'}
              onClick={() => onSort('name')}
            >
              {data.representative_title}
            </TableSortLabel>
          </TableCell>
          {data.projects.map(project => (
            <TableCell
              key={project.id}
              align="center"
              sx={{ fontWeight: 700, minWidth: 110, whiteSpace: 'normal', lineHeight: 1.3 }}
            >
              <Tooltip
                title={
                  project.description ? (
                    <Box>
                      <Typography variant="body2" fontWeight={700}>
                        {project.title}
                      </Typography>
                      <Typography variant="body2" sx={{ mt: 0.5 }}>
                        {project.description}
                      </Typography>
                    </Box>
                  ) : (
                    ''
                  )
                }
                arrow
              >
                <TableSortLabel
                  active={sortField === project.id}
                  direction={sortField === project.id ? sortDirection : 'asc'}
                  onClick={() => onSort(project.id)}
                >
                  {project.title}
                  <MuiLink
                    component={RouterLink}
                    to={`/projects/${project.id}`}
                    onClick={(e: React.MouseEvent) => e.stopPropagation()}
                    sx={{ ml: 0.5, lineHeight: 0, color: 'inherit', '&:hover': { color: 'primary.main' } }}
                    title="View project"
                  >
                    <OpenInNewIcon sx={{ fontSize: '0.75rem', verticalAlign: 'middle', opacity: 0.6 }} />
                  </MuiLink>
                </TableSortLabel>
              </Tooltip>
            </TableCell>
          ))}
          <TableCell align="center" sx={{ fontWeight: 700, minWidth: 90 }}>
            <TableSortLabel
              active={sortField === 'score'}
              direction={sortField === 'score' ? sortDirection : 'desc'}
              onClick={() => onSort('score')}
            >
              Score
            </TableSortLabel>
          </TableCell>
        </TableRow>
      </TableHead>
      <TableBody>
        {rows.map(row => (
          <TableRow key={row.entity.id} hover>
            <TableCell>{row.entity.district_name ?? '—'}</TableCell>
            <TableCell>
              <MuiLink
                component={RouterLink}
                to={`/representatives/${row.entity.id}`}
                underline="hover"
                fontWeight={500}
                sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}
              >
                {row.entity.name}
              </MuiLink>
            </TableCell>
            {data.projects.map(project => {
              const statusEntry = row.statuses[project.id];
              if (!statusEntry) return <TableCell key={project.id} />;
              return (
                <TableCell key={project.id} align="center">
                  <Chip
                    label={statusEntry.label}
                    size="small"
                    sx={{
                      backgroundColor: getStatusColor(statusEntry.status),
                      color: '#fff',
                      fontWeight: 600,
                      fontSize: '0.7rem',
                    }}
                  />
                </TableCell>
              );
            })}
            <TableCell align="center">
              <Typography variant="body2" fontWeight={600}>
                {row.aligned_count} / {row.total_scoreable}
              </Typography>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </TableContainer>
);

export default DesktopTable;
