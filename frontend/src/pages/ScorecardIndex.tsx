import React, { useEffect, useState } from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  CircularProgress,
  Container,
  Typography,
} from '@mui/material';
import api from '../services/api';
import ErrorDisplay from '../components/common/ErrorDisplay';

interface Group {
  id: string;
  name: string;
}

function nameToSlug(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

const ScorecardIndex: React.FC = () => {
  const [groups, setGroups] = useState<Group[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Group[]>('/groups/')
      .then(res => {
        setGroups(res.data.filter(g => g.name !== 'Administrators'));
        setLoading(false);
      })
      .catch(() => {
        setError('Failed to load scorecard groups.');
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <ErrorDisplay message={error} />;
  }

  if (!groups || groups.length === 0) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Typography variant="h4" gutterBottom>
          Scorecards
        </Typography>
        <Typography color="text.secondary">No scorecard groups available.</Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Scorecards
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Select a group to view their legislative scorecard.
      </Typography>
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        {groups.map(group => (
          <Card key={group.id} variant="outlined">
            <CardActionArea component={RouterLink} to={`/scorecard/${nameToSlug(group.name)}`}>
              <CardContent>
                <Typography variant="h6">{group.name}</Typography>
              </CardContent>
            </CardActionArea>
          </Card>
        ))}
      </Box>
    </Container>
  );
};

export default ScorecardIndex;
