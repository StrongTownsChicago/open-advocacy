import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import {
  Container,
  Typography,
  Box,
  Button,
  Chip,
  Divider,
  Card,
  CardContent,
  Link,
  CircularProgress,
  Paper,
  Tabs,
  Tab,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import LinkIcon from '@mui/icons-material/Link';
import EditIcon from '@mui/icons-material/Edit';
import { entityService } from '../services/entities';
import { projectService } from '../services/projects';
import { statusService } from '../services/status';
import { jurisdictionService } from '../services/jurisdictions';
import { Project, Entity, EntityStatusRecord, UserRole } from '../types';
import StatusDistribution from '../components/Status/StatusDistribution';
import EntityList from '../components/Entity/EntityList';
import UserEntityProjectSection from '../components/Entity/UserEntityProjectSection';
import ErrorDisplay from '../components/common/ErrorDisplay';
import ConditionalUI from '../components/auth/ConditionalUI';
import EntityDistrictMap from '../components/Entity/EntityDistrictMap';
import { transformEntityFromApi } from '../utils/dataTransformers';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

interface ProjectDetailProps {
  projectId?: string;
  getStatusLabel?: (status: string) => string;
  representativeTitle?: string;
  isDashboard?: boolean;
}

const ProjectDetail: React.FC<ProjectDetailProps> = ({
  projectId,
  getStatusLabel,
  representativeTitle = 'Representative',
  isDashboard = false,
}) => {
  const { id: routeId } = useParams<{ id: string }>();
  const id = projectId || routeId;
  const navigate = useNavigate();
  const [project, setProject] = useState<Project | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loadingEntities, setLoadingEntities] = useState(false);
  const [statusRecords, setStatusRecords] = useState<EntityStatusRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [geojsonByDistrict, setGeojsonByDistrict] = useState<{
    [districtId: string]: GeoJSON.GeoJsonObject;
  }>({});

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;

      setLoading(true);
      setError(null);

      try {
        // Fetch project
        const projectResponse = await projectService.getProject(id);
        setProject(projectResponse.data);

        // Fetch status records for this project
        const statusResponse = await statusService.getStatusRecords(id);
        setStatusRecords(statusResponse.data);
      } catch (err) {
        console.error('Error fetching project data:', err);
        setError('Failed to load project details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  useEffect(() => {
    const fetchEntities = async () => {
      if (!project || !project.jurisdiction_id) return;

      setLoadingEntities(true);
      try {
        const response = await entityService.getEntitiesByJurisdictions(project.jurisdiction_id);
        const transformedEntities = response.data.map(transformEntityFromApi);
        setEntities(transformedEntities);
      } catch (err) {
        console.error('Failed to fetch entities:', err);
      } finally {
        setLoadingEntities(false);
      }
    };

    fetchEntities();
  }, [project]);

  useEffect(() => {
    const fetchGeoJSON = async () => {
      if (!project?.jurisdiction_id) return;
      try {
        const data = await jurisdictionService.getDistrictGeoJSON(project.jurisdiction_id);
        setGeojsonByDistrict(data);
      } catch (err) {
        console.error('Failed to fetch district geojson:', err);
      }
    };
    fetchGeoJSON();
  }, [project]);

  const handleTabChange = (_event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const refreshStatusRecords = async () => {
    if (!id) return;

    try {
      // Fetch raw status records
      const statusResponse = await statusService.getStatusRecords(id);
      setStatusRecords(statusResponse.data);

      // Also refresh the project to get updated status distribution
      const projectResponse = await projectService.getProject(id);
      setProject(projectResponse.data);
    } catch (err) {
      console.error('Error refreshing project data:', err);
    }
  };

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
          getStatusLabel={getStatusLabel}
          representativeTitle={representativeTitle}
        />

        {Object.keys(geojsonByDistrict).length > 0 && entities.length > 0 && (
          <Box mt={3}>
            <EntityDistrictMap
              entities={entities}
              statusRecords={statusRecords}
              geojsonByDistrict={geojsonByDistrict}
              getStatusLabel={getStatusLabel}
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
              getStatusLabel={getStatusLabel}
            />
          ) : (
            <Typography variant="body2" color="text.secondary">
              No status data available yet
            </Typography>
          )}
        </Box>

        <Divider sx={{ my: 4 }} />

        <Box sx={{ width: '100%' }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs value={tabValue} onChange={handleTabChange} aria-label="project tabs">
              <Tab label="Representatives" id="tab-0" />
              <Tab label="Preferred Response" id="tab-1" />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
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
                getStatusLabel={getStatusLabel}
              />
            )}
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Preferred Response Template
                </Typography>

                {project.template_response ? (
                  <Typography variant="body1" whiteSpace="pre-wrap">
                    {project.template_response}
                  </Typography>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No template response has been provided for this project
                  </Typography>
                )}
              </CardContent>
            </Card>
          </TabPanel>
        </Box>
      </Box>
    </Container>
  );
};

export default ProjectDetail;
