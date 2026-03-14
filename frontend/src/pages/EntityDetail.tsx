import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  Grid,
  Paper,
  Chip,
  Divider,
  Button,
  Card,
  CardContent,
  CardActions,
  CircularProgress,
  Avatar,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import PersonIcon from '@mui/icons-material/Person';
import { entityService } from '../services/entities';
import { projectService } from '../services/projects';
import { statusService } from '../services/status';
import { Entity, Project, EntityStatusRecord, EntityStatus } from '../types';
import { getStatusColor, getStatusLabel } from '../utils/statusColors';
import ErrorDisplay from '../components/common/ErrorDisplay';
import EntityContactInfo from '../components/Entity/EntityContactInfo';

const EntityDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [entity, setEntity] = useState<Entity | null>(null);
  const [statusRecords, setStatusRecords] = useState<EntityStatusRecord[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;

      setLoading(true);
      setError(null);

      try {
        // Fetch entity
        const entityResponse = await entityService.getEntity(id);
        setEntity(entityResponse.data);

        // Fetch status records for this entity
        const statusResponse = await statusService.getStatusRecords(undefined, id);
        setStatusRecords(statusResponse.data);

        // Fetch associated projects
        if (statusResponse.data.length > 0) {
          const projectIds = [...new Set(statusResponse.data.map(sr => sr.project_id))];
          const projectPromises = projectIds.map(pid => projectService.getProject(pid));
          const projectResponses = await Promise.all(projectPromises);
          setProjects(projectResponses.map(pr => pr.data));
        }
      } catch (err) {
        console.error('Error fetching entity data:', err);
        setError('Failed to load representative details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Box display="flex" justifyContent="center" py={8}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error || !entity) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <ErrorDisplay
          message={error || 'Representative not found'}
          onRetry={() => navigate('/representatives')}
        />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)} sx={{ mb: 2 }}>
        Back
      </Button>

      <Grid container spacing={4}>
        {/* Entity Information */}
        <Grid size={{ xs: 12, md: 4 }}>
          <Paper sx={{ p: 3, borderRadius: 2, height: '100%' }}>
            <Box display="flex" alignItems="center" mb={2}>
              <Avatar
                src={entity.image_url}
                sx={{
                  width: 64,
                  height: 64,
                  bgcolor: 'primary.main',
                  mr: 2,
                }}
              >
                <PersonIcon sx={{ fontSize: 40 }} />
              </Avatar>
              <Box>
                <Typography variant="h5" component="h1" fontWeight="bold">
                  {entity.name}
                </Typography>
                <Typography variant="subtitle1" color="text.secondary">
                  {entity.title}
                </Typography>
              </Box>
            </Box>

            {entity.district_name && (
              <Chip label={entity.district_name} color="primary" sx={{ mb: 3 }} />
            )}

            <Divider sx={{ my: 2 }} />

            <Typography variant="h6" gutterBottom>
              Contact Information
            </Typography>

            <EntityContactInfo entity={entity} />
          </Paper>
        </Grid>

        {/* Associated Projects */}
        <Grid size={{ xs: 12, md: 8 }}>
          <Paper sx={{ p: 3, borderRadius: 2 }}>
            <Typography variant="h5" gutterBottom>
              Projects & Positions
            </Typography>

            {projects.length === 0 ? (
              <Box py={4} textAlign="center">
                <Typography variant="body1" color="text.secondary">
                  No positions of this representative have been reported for any of your projects
                </Typography>
              </Box>
            ) : (
              <Grid container spacing={3} sx={{ mt: 1, width: '100%' }}>
                {projects.map(project => {
                  const statusRecord = statusRecords.find(
                    sr => sr.project_id === project.id && sr.entity_id === entity.id
                  );

                  const status = statusRecord?.status || EntityStatus.UNKNOWN;

                  return (
                    <Grid size={{ xs: 12 }} key={project.id} sx={{ width: '100%' }}>
                      <Card
                        sx={{
                          borderLeft: `4px solid ${getStatusColor(status)}`,
                          borderRadius: '0 8px 8px 0',
                          width: '100%',
                          display: 'flex',
                          flexDirection: 'column',
                        }}
                      >
                        <CardContent sx={{ flexGrow: 1 }}>
                          <Box
                            display="flex"
                            justifyContent="space-between"
                            alignItems="flex-start"
                            mb={1}
                          >
                            <Typography
                              variant="h6"
                              sx={{
                                cursor: 'pointer',
                                '&:hover': {
                                  textDecoration: 'underline',
                                  color: 'primary.main',
                                },
                              }}
                              onClick={() => navigate(`/projects/${project.id}`)}
                            >
                              {project.title}
                            </Typography>
                            <Chip
                              label={getStatusLabel(status)}
                              size="small"
                              sx={{
                                bgcolor: getStatusColor(status),
                                color: '#fff',
                              }}
                            />
                          </Box>

                          <Typography
                            variant="body2"
                            color="text.secondary"
                            sx={{
                              mb: 2,
                              display: '-webkit-box',
                              overflow: 'hidden',
                              WebkitBoxOrient: 'vertical',
                              WebkitLineClamp: 2,
                            }}
                          >
                            {project.description}
                          </Typography>

                          {statusRecord?.notes && (
                            <Box
                              sx={{
                                mt: 2,
                                p: 1.5,
                                bgcolor: 'rgba(0,0,0,0.03)',
                                borderRadius: 1,
                              }}
                            >
                              <Typography variant="body2">
                                <strong>Notes:</strong> {statusRecord.notes}
                              </Typography>
                            </Box>
                          )}
                        </CardContent>
                        <CardActions>
                          <Button
                            size="small"
                            variant="contained"
                            color="primary"
                            onClick={() => navigate(`/projects/${project.id}`)}
                          >
                            View Project
                          </Button>
                        </CardActions>
                      </Card>
                    </Grid>
                  );
                })}
              </Grid>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default EntityDetail;
