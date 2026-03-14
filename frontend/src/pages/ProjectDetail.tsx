import React from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import {
  Container,
  Typography,
  Box,
  Button,
  Chip,
  Divider,
  Link,
  CircularProgress,
  Paper,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import LinkIcon from '@mui/icons-material/Link';
import EditIcon from '@mui/icons-material/Edit';
import { UserRole } from '../types';
import StatusDistribution from '../components/Status/StatusDistribution';
import EntityList from '../components/Entity/EntityList';
import UserEntityProjectSection from '../components/Entity/UserEntityProjectSection';
import ErrorDisplay from '../components/common/ErrorDisplay';
import ConditionalUI from '../components/auth/ConditionalUI';
import EntityDistrictMap from '../components/Entity/EntityDistrictMap';
import { useProjectData } from '../hooks/useProjectData';

interface ProjectDetailProps {
  projectId?: string;
  getStatusLabel?: (status: string) => string;
  representativeTitle?: string;
  isDashboard?: boolean;
}

const ProjectDetail: React.FC<ProjectDetailProps> = ({
  projectId,
  representativeTitle = 'Representative',
  isDashboard = false,
}) => {
  const { id: routeId } = useParams<{ id: string }>();
  const id = projectId || routeId;
  const navigate = useNavigate();

  const {
    project,
    entities,
    statusRecords,
    geojsonByDistrict,
    loading,
    loadingEntities,
    error,
    refreshStatusRecords,
  } = useProjectData(id);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" py={8}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error || !project) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <ErrorDisplay
          message={error || 'Project not found'}
          onRetry={() => navigate('/projects')}
        />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box mb={4}>
        {!isDashboard && (
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/projects')}
            sx={{ mb: 2 }}
          >
            Back to Projects
          </Button>
        )}

        <Box display="flex" justifyContent="space-between" alignItems="flex-start">
          <Box>
            {!isDashboard && (
              <Typography variant="h4" component="h1" fontWeight="700" color="text.primary">
                {project.title}
              </Typography>
            )}

            <Box display="flex" alignItems="center" gap={1} my={1}>
              <Chip
                label={project.status.charAt(0).toUpperCase() + project.status.slice(1)}
                color={project.status === 'active' ? 'success' : 'default'}
                size="small"
              />

              {project.link && (
                <Link href={project.link} target="_blank" rel="noopener noreferrer">
                  <Chip
                    icon={<LinkIcon />}
                    label="Project Link"
                    color="primary"
                    variant="outlined"
                    size="small"
                    clickable
                  />
                </Link>
              )}
            </Box>
          </Box>

          <ConditionalUI
            requireAuth={true}
            requiredRoles={[UserRole.EDITOR, UserRole.GROUP_ADMIN, UserRole.SUPER_ADMIN]}
          >
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={() => navigate(`/projects/${id}/edit`)}
            >
              Edit Project
            </Button>
          </ConditionalUI>
        </Box>

        {!isDashboard && (
          <Typography variant="body1" color="text.secondary" paragraph mt={2}>
            <ReactMarkdown
              components={{
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                a: ({ node, ...props }) => (
                  <Link {...props} target="_blank" rel="noopener noreferrer" color="primary" />
                ),
                // eslint-disable-next-line @typescript-eslint/no-unused-vars
                p: ({ node, ...props }) => <span {...props} />,
              }}
            >
              {project.description}
            </ReactMarkdown>
          </Typography>
        )}

        <UserEntityProjectSection
          project={project}
          statusRecords={statusRecords}
          representativeTitle={representativeTitle}
        />

        {Object.keys(geojsonByDistrict).length > 0 && entities.length > 0 && (
          <Box mt={3}>
            <EntityDistrictMap
              entities={entities}
              statusRecords={statusRecords}
              geojsonByDistrict={geojsonByDistrict}
              dashboardConfig={project.dashboard_config}
            />
          </Box>
        )}

        <Box mt={3}>
          {project.status_distribution ? (
            <StatusDistribution
              distribution={project.status_distribution}
              size="large"
              showPercentages
              showCounts
              showLabels
              statusLabels={project.dashboard_config?.status_labels}
            />
          ) : (
            <Typography variant="body2" color="text.secondary">
              No status data available yet
            </Typography>
          )}
        </Box>

        <Divider sx={{ my: 4 }} />

        {loadingEntities ? (
          <Box display="flex" justifyContent="center" py={4}>
            <CircularProgress />
          </Box>
        ) : entities.length === 0 ? (
          <Paper sx={{ p: 4, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              No representatives found for the selected jurisdiction
            </Typography>
          </Paper>
        ) : (
          <EntityList
            entities={entities}
            project={project}
            statusRecords={statusRecords}
            onStatusUpdated={refreshStatusRecords}
          />
        )}
      </Box>
    </Container>
  );
};

export default ProjectDetail;
