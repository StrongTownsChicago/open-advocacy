import React, { useEffect, useState, useMemo } from 'react';
import { useParams } from 'react-router-dom';
import {
  Box,
  CircularProgress,
  Container,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';
import ErrorDisplay from '../../components/common/ErrorDisplay';
import { STATUS_SORT_ORDER } from '../../components/Entity/entitySort';
import { scorecardService } from '../../services/scorecard';
import { EntityStatus, ScorecardEntityRow, ScorecardResponse } from '../../types';
import { compareDistrictNames } from '../../utils/districtSort';
import DesktopTable from './DesktopTable';
import MobileCardList from './MobileCardList';

type SortField = string;
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
    rows.sort((a: ScorecardEntityRow, b: ScorecardEntityRow) => {
      let comparison = 0;
      if (sortField === 'name') {
        comparison = a.entity.name.localeCompare(b.entity.name);
      } else if (sortField === 'ward') {
        comparison = compareDistrictNames(a.entity.district_name, b.entity.district_name);
      } else if (sortField === 'score') {
        const aScore = a.total_scoreable > 0 ? a.aligned_count / a.total_scoreable : 0;
        const bScore = b.total_scoreable > 0 ? b.aligned_count / b.total_scoreable : 0;
        comparison = aScore - bScore;
        if (comparison === 0) {
          comparison = a.entity.name.localeCompare(b.entity.name);
        }
      } else {
        // Sort by a specific project's status (sortField is the project UUID)
        const aRank = STATUS_SORT_ORDER[a.statuses[sortField]?.status ?? EntityStatus.UNKNOWN] ?? 5;
        const bRank = STATUS_SORT_ORDER[b.statuses[sortField]?.status ?? EntityStatus.UNKNOWN] ?? 5;
        comparison = aRank - bRank;
      }
      return sortDirection === 'asc' ? comparison : -comparison;
    });
    return rows;
  }, [data, sortField, sortDirection]);

  const handleSort = (field: string) => {
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
          Scorecard
        </Typography>
        <Typography color="text.secondary">No scorecard data available.</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom fontWeight={700}>
        {data.group_name} — {data.representative_title} Scorecard
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

export default Scorecard;
