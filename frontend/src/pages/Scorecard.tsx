import React, { useEffect, useState, useMemo } from 'react';
import { Link as RouterLink, useParams } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TableSortLabel,
  Tooltip,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import ErrorDisplay from '../components/common/ErrorDisplay';
import { scorecardService } from '../services/scorecard';
import { ScorecardEntityRow, ScorecardResponse } from '../types';
import { getStatusColor } from '../utils/statusColors';

type SortField = 'name' | 'ward' | 'score';
type SortDirection = 'asc' | 'desc';

const Scorecard: React.FC = () => {
  const [data, setData] = useState<ScorecardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortField, setSortField] = useState<SortField>('score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const { groupSlug } = useParams<{ groupSlug: string }>();

  useEffect(() => {
    if (!groupSlug) return;

    const fetchScorecard = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await scorecardService.getScorecard(groupSlug);
        setData(response.data);
      } catch {
        setError('Failed to load scorecard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchScorecard();
  }, [groupSlug]);

  const sortedEntities = useMemo(() => {
    if (!data) return [];
    const rows = [...data.entities];
    rows.sort((a, b) => {
      let comparison = 0;
      if (sortField === 'name') {
        comparison = a.entity.name.localeCompare(b.entity.name);
      } else if (sortField === 'ward') {
        comparison = (a.entity.district_name ?? '').localeCompare(b.entity.district_name ?? '');
      } else {
        // Sort by alignment score ratio (aligned / total), then by name as tiebreaker
        const aScore = a.total_scoreable > 0 ? a.aligned_count / a.total_scoreable : 0;
        const bScore = b.total_scoreable > 0 ? b.aligned_count / b.total_scoreable : 0;
        comparison = aScore - bScore;
        if (comparison === 0) {
          comparison = a.entity.name.localeCompare(b.entity.name);
        }
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });
    return rows;
  }, [data, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(d => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortField(field);
      setSortDirection(field === 'score' ? 'desc' : 'asc');
    }
  };

  if (loading) {
    return (
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '50vh',
        }}
      >
        <CircularProgress size={48} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading scorecard…
        </Typography>
      </Box>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <ErrorDisplay message={error} onRetry={() => window.location.reload()} />
      </Container>
    );
  }

  if (!data || data.entities.length === 0) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom>
          Alderperson Scorecard
        </Typography>
        <Typography color="text.secondary">No scorecard data available.</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight={700}>
        {data.group_name} — Alderperson Scorecard
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Tracks positions across {data.projects.length} issues.
      </Typography>

      {isMobile ? (
        <MobileCardList rows={sortedEntities} data={data} />
      ) : (
        <DesktopTable
          rows={sortedEntities}
          data={data}
          sortField={sortField}
          sortDirection={sortDirection}
          onSort={handleSort}
        />
      )}
    </Container>
  );
};

interface TableProps {
  rows: ScorecardEntityRow[];
  data: ScorecardResponse;
  sortField: SortField;
  sortDirection: SortDirection;
  onSort: (field: SortField) => void;
}

const DesktopTable: React.FC<TableProps> = ({ rows, data, sortField, sortDirection, onSort }) => (
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
              Alderperson
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
                <span>{project.title}</span>
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
              <RouterLink
                to={`/representatives/${row.entity.id}`}
                style={{ color: 'inherit', textDecoration: 'none', fontWeight: 500 }}
              >
                {row.entity.name}
              </RouterLink>
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

interface MobileCardListProps {
  rows: ScorecardEntityRow[];
  data: ScorecardResponse;
}

const MobileCardList: React.FC<MobileCardListProps> = ({ rows, data }) => (
  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
    {rows.map(row => (
      <Card key={row.entity.id} variant="outlined">
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <RouterLink
              to={`/representatives/${row.entity.id}`}
              style={{
                fontWeight: 700,
                fontSize: '1rem',
                textDecoration: 'none',
                color: 'inherit',
              }}
            >
              {row.entity.name}
            </RouterLink>
            <Typography variant="body2" color="text.secondary">
              {row.entity.district_name ?? ''}
            </Typography>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            Alignment: {row.aligned_count} / {row.total_scoreable}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {data.projects.map(project => {
              const statusEntry = row.statuses[project.id];
              if (!statusEntry) return null;
              return (
                <Box
                  key={project.id}
                  sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <Typography variant="caption" sx={{ flex: 1, mr: 1 }}>
                    {project.title}
                  </Typography>
                  <Chip
                    label={statusEntry.label}
                    size="small"
                    sx={{
                      backgroundColor: getStatusColor(statusEntry.status),
                      color: '#fff',
                      fontWeight: 600,
                      fontSize: '0.65rem',
                    }}
                  />
                </Box>
              );
            })}
          </Box>
        </CardContent>
      </Card>
    ))}
  </Box>
);

export default Scorecard;
