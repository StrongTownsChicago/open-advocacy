import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Paper,
  InputBase,
  FormControl,
  Select,
  MenuItem,
  Chip,
  Button,
  CircularProgress,
  SelectChangeEvent,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import SearchIcon from '@mui/icons-material/Search';
import PeopleIcon from '@mui/icons-material/People';
import AccessTimeIcon from '@mui/icons-material/AccessTime';

import { projectService } from '../services/projects';
import { Project, ProjectStatus, UserRole } from '../types';
import ErrorDisplay from '../components/common/ErrorDisplay';
import ConditionalUI from '../components/auth/ConditionalUI';
import { transformProjectFromApi } from '../utils/dataTransformers';
import StatusDistribution from '../components/Status/StatusDistribution';
import { useDebounce } from '../hooks/useDebounce';

const ProjectList: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('all');

  // Debounce search term to avoid too many API calls
  const debouncedSearchTerm = useDebounce(searchTerm, 500);

  const navigate = useNavigate();

  const fetchProjects = async (status?: ProjectStatus | string, searchQuery?: string) => {
    setLoading(true);
    setError(null);
    try {
      const filters: Record<string, string> = {};

      // Only add status filter if it's not "all"
      if (status && status !== 'all') {
        filters.status = status;
      }

      const response = await projectService.getProjects(filters);
      const transformedProjects = response.data.map(transformProjectFromApi);

      // Filter by search term locally (since backend doesn't support text search)
      let projects = transformedProjects;
      if (searchQuery) {
        projects = transformedProjects.filter(
          project =>
            project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            project.description?.toLowerCase().includes(searchQuery.toLowerCase())
        );
      }

      setProjects(projects);
    } catch (err) {
      console.error('Error fetching projects:', err);
      setError('Failed to load projects. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  // Fetch projects on initial load
  useEffect(() => {
    fetchProjects();
  }, []);

  // Refetch when status filter changes
  useEffect(() => {
    fetchProjects(statusFilter as ProjectStatus, debouncedSearchTerm);
  }, [statusFilter, debouncedSearchTerm]);

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(event.target.value);
  };

  const handleStatusFilterChange = (event: SelectChangeEvent) => {
    setStatusFilter(event.target.value);
  };

  const renderStatusChip = (status: ProjectStatus) => {
    let color: 'success' | 'default' | 'warning' | 'secondary' = 'default';

    switch (status) {
      case ProjectStatus.ACTIVE:
        color = 'success';
        break;
      case ProjectStatus.DRAFT:
        color = 'default';
        break;
      case ProjectStatus.COMPLETED:
        color = 'secondary';
        break;
      case ProjectStatus.ARCHIVED:
        color = 'warning';
        break;
    }

    return (
      <Chip label={status.charAt(0).toUpperCase() + status.slice(1)} color={color} size="small" />
    );
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

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <ErrorDisplay message={error} onRetry={() => fetchProjects()} />
      </Container>
    );
  }

  const renderList = () => {
    return (
      <Box sx={{ width: '100%' }}>
        {projects.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="h6" color="text.secondary">
              No projects found matching your criteria
            </Typography>
            <Typography variant="body2" color="text.secondary" mt={1}>
              Try adjusting your search or filter settings
            </Typography>
          </Box>
        ) : (
          projects.map(project => (
            <Paper
              key={project.id}
              sx={{
                p: 3,
                mb: 3,
                borderRadius: 2,
                transition: 'box-shadow 0.2s ease-in-out',
                '&:hover': {
                  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
                },
              }}
            >
              <Box>
                <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={1}>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography
                      variant="h6"
                      fontWeight="600"
                      sx={{ cursor: 'pointer' }}
                      onClick={() => navigate(`/projects/${project.id}`)}
                    >
                      {project.title}
                    </Typography>
                    {renderStatusChip(project.status)}
                  </Box>
                </Box>

                <Typography variant="body2" color="text.secondary" mb={2}>
                  {project.description}
                </Typography>

                {project.status_distribution && (
                  <Box mb={2}>
                    <StatusDistribution
                      distribution={project.status_distribution}
                      size="small"
                      showCounts={true}
                      showLabels={true}
                    />
                  </Box>
                )}

                <Box display="flex" alignItems="center" gap={2} mb={2}>
                  {project.jurisdiction_name && (
                    <Chip label={project.jurisdiction_name} size="small" variant="outlined" />
                  )}

                  <Box display="flex" alignItems="center" gap={0.5}>
                    <PeopleIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      {project.status_distribution?.total || 0} Representatives
                    </Typography>
                  </Box>

                  <Box display="flex" alignItems="center" gap={0.5}>
                    <AccessTimeIcon fontSize="small" color="action" />
                    <Typography variant="body2" color="text.secondary">
                      Updated: {new Date(project.updated_at).toLocaleDateString()}
                    </Typography>
                  </Box>
                </Box>

                <Box display="flex" gap={1}>
                  <Button
                    variant="outlined"
                    size="small"
                    onClick={() => navigate(`/projects/${project.id}`)}
                  >
                    View Details
                  </Button>
                </Box>
              </Box>
            </Paper>
          ))
        )}
      </Box>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box mb={4}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h4" component="h1" fontWeight="700" color="text.primary">
            Advocacy Projects
          </Typography>

          <ConditionalUI
            requireAuth={true}
            requiredRoles={[UserRole.EDITOR, UserRole.GROUP_ADMIN, UserRole.SUPER_ADMIN]}
          >
            <Button
              variant="contained"
              color="primary"
              onClick={() => navigate('/projects/create')}
            >
              Create Project
            </Button>
          </ConditionalUI>
        </Box>

        <Typography variant="body1" color="text.secondary" mb={4}>
          Browse projects, check their status, and find ways to support causes you care about.
        </Typography>

        <Box
          display="flex"
          alignItems="center"
          gap={2}
          mb={4}
          sx={{
            flexDirection: { xs: 'column', sm: 'row' },
            alignItems: { xs: 'stretch', sm: 'center' },
          }}
        >
          <Box
            sx={{
              position: 'relative',
              width: '100%',
            }}
          >
            <SearchIcon
              sx={{
                position: 'absolute',
                left: 12,
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'action.active',
              }}
            />
            <InputBase
              placeholder="Search projects"
              value={searchTerm}
              onChange={handleSearchChange}
              sx={{
                width: '100%',
                pl: 5,
                pr: 2,
                py: 1,
                border: '1px solid',
                borderColor: 'divider',
                borderRadius: 1,
              }}
            />
          </Box>

          <Box
            sx={{
              display: 'flex',
              justifyContent: { xs: 'flex-end', sm: 'flex-end' },
              width: { xs: '100%', sm: 'auto' },
            }}
          >
            <FormControl size="small" sx={{ minWidth: 140 }}>
              <Select
                value={statusFilter}
                onChange={handleStatusFilterChange}
                displayEmpty
                inputProps={{ 'aria-label': 'Filter by Status' }}
                renderValue={selected => (
                  <Box display="flex" alignItems="center">
                    <Typography variant="body2">
                      {selected === 'all'
                        ? 'All Statuses'
                        : selected.charAt(0).toUpperCase() + selected.slice(1)}
                    </Typography>
                  </Box>
                )}
                sx={{ height: '40px' }}
              >
                <MenuItem value="all">All Statuses</MenuItem>
                <MenuItem value={ProjectStatus.ACTIVE}>Active</MenuItem>
                <MenuItem value={ProjectStatus.DRAFT}>Draft</MenuItem>
                <MenuItem value={ProjectStatus.COMPLETED}>Completed</MenuItem>
                <MenuItem value={ProjectStatus.ARCHIVED}>Archived</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Box>
      </Box>

      {renderList()}
    </Container>
  );
};

export default ProjectList;
