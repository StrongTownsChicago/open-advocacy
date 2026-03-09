import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  TextField,
  Button,
  Paper,
  Box,
  CircularProgress,
  Alert,
  MenuItem,
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import VolunteerActivismIcon from '@mui/icons-material/VolunteerActivism';
import { groupService } from '../../services/groups';
import { appConfig } from '@/utils/config';

interface Group {
  id: string;
  name: string;
  description?: string;
}

const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [groupId, setGroupId] = useState('');
  const [role, setRole] = useState('editor');
  const [groups, setGroups] = useState<Group[]>([]);
  const [loading, setLoading] = useState(false);
  const [formErrors, setFormErrors] = useState<{
    email?: string;
    name?: string;
    password?: string;
    confirmPassword?: string;
    groupId?: string;
    role?: string;
  }>({});
  const [serverError, setServerError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const { register, isAuthenticated, hasRole } = useAuth();
  const navigate = useNavigate();

  // Check if user is already authenticated and has admin role
  useEffect(() => {
    if (isAuthenticated && !hasRole('super_admin') && !hasRole('group_admin')) {
      // Only admin users can register new users
      navigate('/');
    }
  }, [isAuthenticated, hasRole, navigate]);

  // Fetch available groups
  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const response = await groupService.getGroups();
        setGroups(response.data);

        // TODO: Have better validation on group selection
        // If there's only one group, auto-select it
        if (response.data.length === 1) {
          setGroupId(response.data[0].id);
        }
      } catch (error) {
        console.error('Failed to fetch groups:', error);
        setServerError('Failed to load available groups. Please try again later.');
      }
    };

    fetchGroups();
  }, []);

  const validateForm = (): boolean => {
    const errors: {
      email?: string;
      name?: string;
      password?: string;
      confirmPassword?: string;
      groupId?: string;
      role?: string;
    } = {};

    if (!email) {
      errors.email = 'Email is required';
    } else if (!/\S+@\S+\.\S+/.test(email)) {
      errors.email = 'Invalid email format';
    }

    if (!name) {
      errors.name = 'Full name is required';
    }

    if (!password) {
      errors.password = 'Password is required';
    } else if (password.length < 8) {
      errors.password = 'Password must be at least 8 characters';
    }

    if (password !== confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }

    if (!groupId) {
      errors.groupId = 'Please select a group';
    }

    if (!role) {
      errors.role = 'Please select a role';
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setServerError(null);

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const userData = {
        email,
        name,
        password,
        group_id: groupId,
        is_active: true,
        role,
      };

      const result = await register(userData);

      if (result) {
        setSuccess(true);
        // Reset form
        setEmail('');
        setName('');
        setPassword('');
        setConfirmPassword('');
        setGroupId('');
        setRole('editor');
      } else {
        setServerError('Registration failed. Please try again.');
      }
    } catch (error: unknown) {
      console.error('Registration error:', error);
      const errorMessage =
        (error instanceof Error && 'response' in error
          ? (error as { response?: { data?: { detail?: string } } }).response?.data?.detail
          : undefined) || 'An unexpected error occurred. Please try again later.';
      setServerError(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          mt: 8,
          mb: 4,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <VolunteerActivismIcon color="primary" sx={{ width: 56, height: 56, mb: 2 }} />

        <Typography component="h1" variant="h4" gutterBottom sx={{ textAlign: 'center' }}>
          {appConfig.name}
        </Typography>

        <Paper
          elevation={3}
          sx={{
            p: 4,
            width: '100%',
            mt: 3,
            borderRadius: 2,
          }}
        >
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
            }}
          >
            <Box
              sx={{
                backgroundColor: 'primary.main',
                borderRadius: '50%',
                p: 1,
                mb: 2,
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
              }}
            >
              <PersonAddIcon sx={{ color: 'white' }} />
            </Box>

            <Typography component="h2" variant="h5" gutterBottom>
              Register New User
            </Typography>

            {serverError && (
              <Alert severity="error" sx={{ width: '100%', mb: 2 }}>
                {serverError}
              </Alert>
            )}

            {success && (
              <Alert severity="success" sx={{ width: '100%', mb: 2 }}>
                User registered successfully!
              </Alert>
            )}

            <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%', mt: 1 }}>
              <TextField
                margin="normal"
                required
                fullWidth
                id="email"
                label="Email Address"
                name="email"
                autoComplete="email"
                value={email}
                onChange={e => setEmail(e.target.value)}
                error={!!formErrors.email}
                helperText={formErrors.email}
                disabled={loading}
              />

              <TextField
                margin="normal"
                required
                fullWidth
                id="name"
                label="Full Name"
                name="name"
                autoComplete="name"
                value={name}
                onChange={e => setName(e.target.value)}
                error={!!formErrors.name}
                helperText={formErrors.name}
                disabled={loading}
              />

              <TextField
                margin="normal"
                required
                fullWidth
                name="password"
                label="Password"
                type="password"
                id="password"
                autoComplete="new-password"
                value={password}
                onChange={e => setPassword(e.target.value)}
                error={!!formErrors.password}
                helperText={formErrors.password}
                disabled={loading}
              />

              <TextField
                margin="normal"
                required
                fullWidth
                name="confirmPassword"
                label="Confirm Password"
                type="password"
                id="confirmPassword"
                autoComplete="new-password"
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                error={!!formErrors.confirmPassword}
                helperText={formErrors.confirmPassword}
                disabled={loading}
              />

              <TextField
                select
                margin="normal"
                required
                fullWidth
                id="groupId"
                label="Group"
                name="groupId"
                value={groupId}
                onChange={e => setGroupId(e.target.value)}
                error={!!formErrors.groupId}
                helperText={formErrors.groupId || 'Select the group for this user'}
                disabled={loading || groups.length === 0}
              >
                {groups.map(group => (
                  <MenuItem key={group.id} value={group.id}>
                    {group.name}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                select
                margin="normal"
                required
                fullWidth
                id="role"
                label="User Role"
                name="role"
                value={role}
                onChange={e => setRole(e.target.value)}
                error={!!formErrors.role}
                helperText={formErrors.role || 'Select the role for this user'}
                disabled={loading}
              >
                <MenuItem value="group_admin">Group Admin</MenuItem>
                <MenuItem value="editor">Editor</MenuItem>
              </TextField>

              <Button
                type="submit"
                fullWidth
                variant="contained"
                sx={{ mt: 3, mb: 2, py: 1.5 }}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Register User'}
              </Button>
            </Box>
          </Box>
        </Paper>

        <Box mt={3} textAlign="center">
          <Button component={RouterLink} to="/" variant="text" color="primary">
            Back to Home
          </Button>
        </Box>
      </Box>
    </Container>
  );
};

export default RegisterPage;
