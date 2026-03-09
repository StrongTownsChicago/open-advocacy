import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography } from '@mui/material';
import { projectService } from '../../services/projects';
import ProjectDetail from '../ProjectDetail';

const STATUS_DISPLAY_NAMES: Record<string, string> = {
  solid_approval: 'Fully Opted In',
  leaning_approval: 'Partially Opted In',
  neutral: 'Not Eligible',
  leaning_disapproval: 'Not Opted In',
  solid_disapproval: 'Strongly Opposed',
  unknown: 'Unknown',
};

const ADU_PROJECT_NAME = 'ADU Opt-In Dashboard';

const AduOptInDashboard: React.FC = () => {
  const [projectId, setProjectId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProjectId = async () => {
      setLoading(true);
      setError(null);
      try {
        const response = await projectService.getProjectByName(ADU_PROJECT_NAME);
        if (response.data) {
          setProjectId(response.data.id);
        } else {
          setError('ADU Opt-In project not found');
        }
      } catch {
        setError('Failed to load ADU Opt-In project');
      } finally {
        setLoading(false);
      }
    };
    fetchProjectId();
  }, []);

  const getCustomStatusLabel = (status: string) => STATUS_DISPLAY_NAMES[status] || 'Unknown';

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
          Loading ADU Opt-In Dashboard...
        </Typography>
      </Box>
    );
  }

  if (error || !projectId) {
    return (
      <div>
        <p>{error || 'Project not found.'}</p>
        <button onClick={() => navigate('/projects')}>Back to Projects</button>
      </div>
    );
  }

  return (
    <ProjectDetail
      projectId={projectId}
      getStatusLabel={getCustomStatusLabel}
      representativeTitle="Alderperson"
      isDashboard={true}
    />
  );
};

export default AduOptInDashboard;
