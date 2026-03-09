import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  FormHelperText,
  Divider,
  IconButton,
  Tooltip,
  Paper,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import InfoOutlinedIcon from '@mui/icons-material/InfoOutlined';
import { ProjectStatus, EntityStatus, Project, ProjectCreateData, Jurisdiction } from '../../types';
import { jurisdictionService } from '../../services/jurisdictions';
import { groupService } from '../../services/groups';

interface ProjectFormProps {
  project?: Project;
  onSubmit?: (project: ProjectCreateData) => void;
  onCancel?: () => void;
}

const ProjectForm: React.FC<ProjectFormProps> = ({ project, onSubmit, onCancel }) => {
  const [title, setTitle] = useState(project?.title || '');
  const [description, setDescription] = useState(project?.description || '');
  const [status, setStatus] = useState<ProjectStatus>(project?.status || ProjectStatus.DRAFT);
  const [link, setLink] = useState(project?.link || '');
  const [preferredStatus, setPreferredStatus] = useState<EntityStatus>(
    project?.preferred_status || EntityStatus.SOLID_APPROVAL
  );
  const [templateResponse, setTemplateResponse] = useState(project?.template_response || '');
  const [jurisdictionId, setJurisdictionId] = useState<string>(project?.jurisdiction_id || '');
  const [groupId, setGroupId] = useState<string>(project?.group_id || '');

  const [titleError, setTitleError] = useState('');
  const [jurisdictionError, setJurisdictionError] = useState('');

  const [jurisdictions, setJurisdictions] = useState<Jurisdiction[]>([]);
  const [groups, setGroups] = useState<{ id: string; name: string }[]>([]);
  const [loading, setLoading] = useState(false);
  const [, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [jurisdictionsResponse, groupsResponse] = await Promise.all([
          jurisdictionService.getJurisdictions(),
          groupService.getGroups(),
        ]);
        setJurisdictions(jurisdictionsResponse.data);
        setGroups(groupsResponse.data);
      } catch (err) {
        console.error('Error fetching form data:', err);
        setError('Failed to load form data');
      }
    };

    fetchData();
  }, []);

  const validateForm = () => {
    let isValid = true;

    // Validate title
    if (!title.trim()) {
      setTitleError('Title is required');
      isValid = false;
    } else {
      setTitleError('');
    }

    // Validate jurisdiction
    if (!jurisdictionId) {
      setJurisdictionError('Jurisdiction is required');
      isValid = false;
    } else {
      setJurisdictionError('');
    }

    return isValid;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const projectData = {
        title,
        description,
        status,
        active: true,
        link,
        preferred_status: preferredStatus,
        template_response: templateResponse,
        jurisdiction_id: jurisdictionId,
        group_id: groupId || undefined,
      };

      if (onSubmit) {
        onSubmit(projectData);
      }
    } catch (err) {
      console.error('Error saving project:', err);
      setError('Failed to save project');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 2,
        border: '1px solid',
        borderColor: 'divider',
        overflow: 'hidden',
      }}
    >
      <Box
        sx={{
          p: 3,
          borderBottom: '1px solid',
          borderColor: 'divider',
          bgcolor: 'background.paper',
        }}
      >
        <Typography variant="h5" component="h2" fontWeight="600">
          {project ? 'Edit Project' : 'Create New Project'}
        </Typography>
      </Box>

      <Box component="form" onSubmit={handleSubmit} sx={{ p: 3 }}>
        {/* BASIC INFORMATION SECTION */}
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="subtitle1"
            component="h3"
            fontWeight="600"
            color="primary"
            sx={{ mb: 2 }}
          >
            Basic Information
          </Typography>

          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 8 }}>
              <TextField
                fullWidth
                required
                id="title"
                name="title"
                label="Title"
                value={title}
                onChange={e => setTitle(e.target.value)}
                error={!!titleError}
                helperText={titleError || 'Give your project a clear, actionable name'}
              />
            </Grid>

            <Grid size={{ xs: 12, md: 4 }}>
              <FormControl fullWidth>
                <InputLabel id="status-label">Status</InputLabel>
                <Select
                  labelId="status-label"
                  id="status"
                  value={status}
                  label="Status"
                  onChange={e => setStatus(e.target.value as ProjectStatus)}
                  MenuProps={{
                    PaperProps: {
                      sx: { maxHeight: 48 * 4.5 },
                    },
                  }}
                >
                  <MenuItem value={ProjectStatus.DRAFT}>Draft</MenuItem>
                  <MenuItem value={ProjectStatus.ACTIVE}>Active</MenuItem>
                  <MenuItem value={ProjectStatus.COMPLETED}>Completed</MenuItem>
                  <MenuItem value={ProjectStatus.ARCHIVED}>Archived</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                id="description"
                name="description"
                label="Description"
                value={description}
                onChange={e => setDescription(e.target.value)}
                helperText="Describe the project's goals and what you hope to achieve"
              />
            </Grid>

            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                id="link"
                name="link"
                label="External Link"
                value={link}
                onChange={e => setLink(e.target.value)}
                helperText="Optional link to project website or resources"
              />
            </Grid>
          </Grid>
        </Box>

        <Divider sx={{ my: 4 }} />

        {/* ORGANIZATION SECTION */}
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="subtitle1"
            component="h3"
            fontWeight="600"
            color="primary"
            sx={{ mb: 2 }}
          >
            Organization
          </Typography>

          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth error={!!jurisdictionError}>
                <InputLabel id="jurisdiction-label">Jurisdiction</InputLabel>
                <Select
                  labelId="jurisdiction-label"
                  id="jurisdiction"
                  value={jurisdictionId}
                  label="Jurisdiction"
                  onChange={e => setJurisdictionId(e.target.value)}
                  displayEmpty
                  MenuProps={{
                    PaperProps: {
                      sx: { maxHeight: 48 * 4.5 },
                    },
                  }}
                >
                  {jurisdictions.map(jurisdiction => (
                    <MenuItem key={jurisdiction.id} value={jurisdiction.id}>
                      {jurisdiction.name}
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>
                  {jurisdictionError || 'The governmental body this project targets'}
                </FormHelperText>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel id="group-label">Group</InputLabel>
                <Select
                  labelId="group-label"
                  id="group"
                  value={groupId}
                  label="Group"
                  onChange={e => setGroupId(e.target.value)}
                  displayEmpty
                  MenuProps={{
                    PaperProps: {
                      sx: { maxHeight: 48 * 4.5 },
                    },
                  }}
                >
                  {groups.map(group => (
                    <MenuItem key={group.id} value={group.id}>
                      {group.name}
                    </MenuItem>
                  ))}
                </Select>
                <FormHelperText>The advocacy group organizing this project</FormHelperText>
              </FormControl>
            </Grid>
          </Grid>
        </Box>

        <Divider sx={{ my: 4 }} />

        {/* ADVOCACY SETTINGS SECTION */}
        <Box sx={{ mb: 4 }}>
          <Typography
            variant="subtitle1"
            component="h3"
            fontWeight="600"
            color="primary"
            sx={{ mb: 2 }}
          >
            Advocacy Settings
          </Typography>

          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 6 }}>
              <FormControl fullWidth>
                <InputLabel id="preferred-status-label">Preferred Status</InputLabel>
                <Select
                  labelId="preferred-status-label"
                  id="preferred-status"
                  value={preferredStatus}
                  label="Preferred Status"
                  onChange={e => setPreferredStatus(e.target.value as EntityStatus)}
                  MenuProps={{
                    PaperProps: {
                      sx: { maxHeight: 48 * 4.5 },
                    },
                  }}
                >
                  <MenuItem value={EntityStatus.SOLID_APPROVAL}>Solid Approval</MenuItem>
                  <MenuItem value={EntityStatus.LEANING_APPROVAL}>Leaning Approval</MenuItem>
                  <MenuItem value={EntityStatus.NEUTRAL}>Neutral</MenuItem>
                  <MenuItem value={EntityStatus.LEANING_DISAPPROVAL}>Leaning Disapproval</MenuItem>
                  <MenuItem value={EntityStatus.SOLID_DISAPPROVAL}>Solid Disapproval</MenuItem>
                </Select>
                <Box display="flex" alignItems="center">
                  <FormHelperText>Target status you want representatives to hold</FormHelperText>
                  <Tooltip
                    title="This determines how we measure success with representatives"
                    placement="top"
                  >
                    <IconButton size="small" sx={{ ml: 0.5, p: 0.5 }}>
                      <InfoOutlinedIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </Box>
              </FormControl>
            </Grid>

            <Grid size={{ xs: 12 }}>
              <TextField
                fullWidth
                multiline
                rows={4}
                id="template-response"
                name="template_response"
                label="Template Response"
                value={templateResponse}
                onChange={e => setTemplateResponse(e.target.value)}
                helperText="A template message for advocates to use when contacting representatives"
              />
            </Grid>
          </Grid>
        </Box>

        {/* ACTION BUTTONS */}
        <Box
          sx={{
            display: 'flex',
            justifyContent: 'space-between',
            pt: 2,
            borderTop: '1px solid',
            borderColor: 'divider',
            mt: 4,
          }}
        >
          <Button
            variant="outlined"
            color="inherit"
            onClick={onCancel}
            startIcon={<ArrowBackIcon />}
          >
            Cancel
          </Button>

          <Button type="submit" variant="contained" color="primary" disabled={loading}>
            {loading ? 'Saving...' : project ? 'Update Project' : 'Create Project'}
          </Button>
        </Box>
      </Box>
    </Paper>
  );
};

export default ProjectForm;
