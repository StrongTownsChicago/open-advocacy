import React, { useState, useEffect } from 'react';
import { Container, Typography, Box, Button, CircularProgress } from '@mui/material';
import { useNavigate, useParams } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import ProjectForm from '../components/Project/ProjectForm';
import { Project, ProjectCreateData } from '../types';
import { projectService } from '../services/projects';

const ProjectFormPage: React.FC = () => {
  const { id } = useParams<{ id?: string }>();
  const navigate = useNavigate();
  const isEditing = Boolean(id);
  const [project, setProject] = useState<Project | undefined>(undefined);
  const [loading, setLoading] = useState<boolean>(isEditing);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch project data when editing
    if (isEditing && id) {
      setLoading(true);
      projectService
        .getProject(id)
        .then(response => {
          setProject(response.data);
          setLoading(false);
        })
        .catch(err => {
          console.error('Error fetching project:', err);
          setError('Failed to load project data');
          setLoading(false);
        });
    }
  }, [id, isEditing]);

  const handleSubmit = async (formData: ProjectCreateData) => {
    try {
      let response;

      if (isEditing && id) {
        response = await projectService.updateProject(id, formData);
      } else {
        response = await projectService.createProject(formData);
      }

      // Navigate to the project details page after successful submission
      navigate(`/projects/${response.data.id}`);
    } catch (err) {
      console.error('Error submitting project:', err);
      setError('Failed to save project');
    }
  };

  if (loading) {
    return (
      <Container
        sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '50vh' }}
      >
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box mb={4}>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate('/projects')} sx={{ mb: 2 }}>
          Back to Projects
        </Button>

        <Typography variant="h4" component="h1" fontWeight="700" color="text.primary" gutterBottom>
          {isEditing ? 'Edit Project' : 'Create New Project'}
        </Typography>

        {error && (
          <Typography color="error" sx={{ mb: 2 }}>
            {error}
          </Typography>
        )}
      </Box>

      <ProjectForm
        project={project}
        onSubmit={handleSubmit}
        onCancel={() => navigate('/projects')}
      />
    </Container>
  );
};

export default ProjectFormPage;
