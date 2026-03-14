import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CircularProgress, Box } from '@mui/material';
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
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .get<Group[]>('/groups/')
      .then(res => {
        const groups = res.data;
        if (groups.length === 0) {
          setError('No groups found.');
          return;
        }
        navigate(`/scorecard/${nameToSlug(groups[0].name)}`, { replace: true });
      })
      .catch(() => setError('Failed to load scorecard.'));
  }, [navigate]);

  if (error) return <ErrorDisplay message={error} />;

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
      <CircularProgress />
    </Box>
  );
};

export default ScorecardIndex;
