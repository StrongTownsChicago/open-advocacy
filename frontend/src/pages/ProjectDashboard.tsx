import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Box, CircularProgress, Typography, Button } from '@mui/material';
import { projectService } from '../services/projects';
import { Project } from '../types';
import ProjectDetail from './ProjectDetail';

const ProjectDashboard: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchProject = async () => {
      if (!slug) {
        setError('No dashboard slug provided');
        setLoading(false);
        return;
      }

      setLoading(true);
      setError(null);
      try {
        const response = await projectService.getProjectBySlug(slug);
        if (response.data) {
          setProject(response.data);
        } else {
          setError('Dashboard not found');
        }
      } catch {
        setError('Dashboard not found');
      } finally {
        setLoading(false);
      }
    };
    fetchProject();
  }, [slug]);

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
          Loading dashboard...
        </Typography>
      </Box>
    );
  }

  if (error || !project) {
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
        <Typography variant="h6" color="text.secondary" gutterBottom>
          {error || 'Dashboard not found'}
        </Typography>
        <Button variant="contained" onClick={() => navigate('/projects')}>
          Back to Projects
        </Button>
      </Box>
    );
  }

  const config = project.dashboard_config;

  const getStatusLabel = config?.status_labels
    ? (status: string) => config.status_labels?.[status] || status
    : undefined;

  return (
    <ProjectDetail
      projectId={project.id}
      getStatusLabel={getStatusLabel}
      representativeTitle={config?.representative_title}
      isDashboard={!!config}
    />
  );
};

export default ProjectDashboard;
