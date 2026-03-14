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
  useTheme,
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
  const theme = useTheme();
  const isLight = theme.palette.mode === 'light';

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
          <CircularProgress color="primary" />
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
    <Container maxWidth="lg" sx={{ py: { xs: 2, sm: 4 } }}>
      <Box mb={4}>
        {!isDashboard && (
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/projects')}
            sx={{ mb: 2, color: 'text.secondary', fontWeight: 500 }}
          >
            Back to Projects
          </Button>
        )}

        {/* Header row */}
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box>
            {!isDashboard && (
              <Typography
                variant="h4"
                component="h1"
                sx={{
                  fontFamily: '"Fraunces", Georgia, serif',
                  fontWeight: 700,
                  color: 'text.primary',
                  mb: 0.5,
                }}
              >
                {project.title}
              </Typography>
            )}

            <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
              <Chip
                label={project.status.charAt(0).toUpperCase() + project.status.slice(1)}
                size="small"
                sx={{
                  backgroundColor:
                    project.status === 'active'
                      ? theme.palette.primary.main
                      : isLight
                        ? 'rgba(0,0,0,0.08)'
                        : 'rgba(255,255,255,0.12)',
                  color: project.status === 'active' ? '#fff' : 'text.secondary',
                  fontWeight: 700,
                  fontSize: '0.7rem',
                  letterSpacing: '0.04em',
                  borderRadius: '5px',
                  height: 22,
                }}
              />

              {project.link && (
                <Link href={project.link} target="_blank" rel="noopener noreferrer">
                  <Chip
                    icon={<LinkIcon sx={{ fontSize: '14px !important' }} />}
                    label="Project Link"
                    variant="outlined"
                    size="small"
                    clickable
                    sx={{
                      borderColor: theme.palette.primary.main,
                      color: theme.palette.primary.main,
                      fontWeight: 600,
                      fontSize: '0.7rem',
                      borderRadius: '5px',
                      height: 22,
                      borderWidth: '1.5px',
                    }}
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
              size="small"
              sx={{ ml: 2, flexShrink: 0 }}
            >
              Edit Project
            </Button>
          </ConditionalUI>
        </Box>

        {!isDashboard && project.description && (
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{
              mb: 3,
              lineHeight: 1.7,
              fontSize: '0.95rem',
            }}
          >
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

        {/* Your representative section */}
        <UserEntityProjectSection
          project={project}
          statusRecords={statusRecords}
          representativeTitle={representativeTitle}
        />

        {/* Map section */}
        {Object.keys(geojsonByDistrict).length > 0 && entities.length > 0 && (
          <Box
            sx={{
              mb: 3,
              borderRadius: 2,
              overflow: 'hidden',
              border: `1px solid ${isLight ? 'rgba(0,0,0,0.08)' : 'rgba(255,255,255,0.08)'}`,
              boxShadow: isLight
                ? '0 1px 3px rgba(0,0,0,0.05), 0 4px 16px rgba(0,0,0,0.03)'
                : '0 1px 3px rgba(0,0,0,0.4)',
            }}
          >
            <EntityDistrictMap
              entities={entities}
              statusRecords={statusRecords}
              geojsonByDistrict={geojsonByDistrict}
              dashboardConfig={project.dashboard_config}
            />
          </Box>
        )}

        {/* Status distribution section */}
        {project.status_distribution ? (
          <Box
            sx={{
              p: 3,
              mb: 3,
              borderRadius: 2,
              backgroundColor: isLight ? '#FFFFFF' : theme.palette.background.paper,
              border: `1px solid ${isLight ? 'rgba(0,0,0,0.07)' : 'rgba(255,255,255,0.07)'}`,
            }}
          >
            <StatusDistribution
              distribution={project.status_distribution}
              size="large"
              showPercentages
              showCounts
              showLabels
              statusLabels={project.dashboard_config?.status_labels}
            />
          </Box>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            No status data available yet
          </Typography>
        )}

        <Divider sx={{ my: 4 }} />

        {/* Representatives table section */}
        <Box>
          {loadingEntities ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress color="primary" />
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
      </Box>
    </Container>
  );
};

export default ProjectDetail;
