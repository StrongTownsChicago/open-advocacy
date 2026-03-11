import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Grid,
  Card,
  CardContent,
  CardActionArea,
  Typography,
  CircularProgress,
  Alert,
} from '@mui/material';
import PeopleIcon from '@mui/icons-material/People';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import AssignmentIcon from '@mui/icons-material/Assignment';
import AdminLayout from '../../components/common/AdminLayout';
import { useAuth } from '../../contexts/AuthContext';
import { projectService } from '../../services/projects';

const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [projectCount, setProjectCount] = useState<number | null>(null);
  const [projectError, setProjectError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProjectCount = async () => {
      try {
        const response = await projectService.getProjects();
        setProjectCount(response.data.length);
      } catch {
        setProjectError('Failed to load project count');
      }
    };
    fetchProjectCount();
  }, []);

  const isSuperAdmin = user?.role === 'super_admin';

  const navCards = [
    {
      title: 'User Management',
      description: 'Manage users, roles, and permissions',
      icon: <PeopleIcon sx={{ fontSize: 40 }} />,
      path: '/admin/users',
      visible: true,
    },
    {
      title: 'Register User',
      description: 'Create a new user account',
      icon: <PersonAddIcon sx={{ fontSize: 40 }} />,
      path: '/register',
      visible: true,
    },
    {
      title: 'Data Imports',
      description: 'Import location and representative data',
      icon: <CloudDownloadIcon sx={{ fontSize: 40 }} />,
      path: '/admin/imports',
      visible: isSuperAdmin,
    },
  ];

  return (
    <AdminLayout title="Admin Dashboard">
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card>
            <CardContent sx={{ textAlign: 'center' }}>
              <AssignmentIcon color="primary" sx={{ fontSize: 40, mb: 1 }} />
              <Typography variant="h4" component="div">
                {projectError ? (
                  <Alert severity="error" sx={{ justifyContent: 'center' }}>
                    {projectError}
                  </Alert>
                ) : projectCount !== null ? (
                  projectCount
                ) : (
                  <CircularProgress size={24} />
                )}
              </Typography>
              <Typography color="text.secondary">Projects</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
        Quick Actions
      </Typography>

      <Grid container spacing={3}>
        {navCards
          .filter(card => card.visible)
          .map(card => (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={card.title}>
              <Card>
                <CardActionArea onClick={() => navigate(card.path)} sx={{ p: 2 }}>
                  <CardContent sx={{ textAlign: 'center' }}>
                    {card.icon}
                    <Typography variant="h6" component="div" sx={{ mt: 1 }}>
                      {card.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {card.description}
                    </Typography>
                  </CardContent>
                </CardActionArea>
              </Card>
            </Grid>
          ))}
      </Grid>
    </AdminLayout>
  );
};

export default AdminDashboard;
