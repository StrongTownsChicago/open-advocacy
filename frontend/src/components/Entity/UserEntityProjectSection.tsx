import React, { useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  Button,
  Chip,
  List,
  Avatar,
  useTheme,
  IconButton,
  Collapse,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import KeyboardArrowDownIcon from '@mui/icons-material/KeyboardArrowDown';
import KeyboardArrowUpIcon from '@mui/icons-material/KeyboardArrowUp';
import { useNavigate } from 'react-router-dom';
import { useUserRepresentatives } from '../../contexts/UserRepresentativesContext';
import { Project, EntityStatusRecord, EntityStatus, Entity } from '../../types';
import { getStatusColor, makeStatusLabelFn } from '../../utils/statusColors';
import EntityContactInfo from './EntityContactInfo';

interface RepresentativeItemProps {
  entity: Entity;
  statusRecord?: EntityStatusRecord;
  statusLabels?: Record<string, string>;
}

const RepresentativeItem: React.FC<RepresentativeItemProps> = ({
  entity,
  statusRecord,
  statusLabels,
}) => {
  const [expanded, setExpanded] = useState(false);
  const theme = useTheme();
  const navigate = useNavigate();

  const getStatusLabel = makeStatusLabelFn(statusLabels);
  const status = statusRecord?.status || 'unknown';
  const notes = statusRecord?.notes;

  const handleToggle = () => {
    setExpanded(!expanded);
  };

  return (
    <Box
      sx={{
        mb: 2,
        borderLeft: `4px solid ${getStatusColor(status as EntityStatus)}`,
        borderRadius: '0 4px 4px 0',
        overflow: 'hidden',
        backgroundColor: theme.palette.background.default,
      }}
    >
      {/* Header section - always visible */}
      <Box
        display="flex"
        alignItems="center"
        onClick={handleToggle}
        sx={{
          padding: 2,
          cursor: 'pointer',
          '&:hover': { backgroundColor: 'rgba(0, 0, 0, 0.04)' },
        }}
      >
        <Avatar src={entity.image_url} sx={{ mr: 2, bgcolor: theme.palette.primary.main }}>
          <PersonIcon />
        </Avatar>

        <Box flexGrow={1}>
          <Box display="flex" alignItems="center" mb={0.5}>
            <Typography variant="subtitle1" fontWeight="bold">
              {entity.name}
            </Typography>
            <Chip
              label={getStatusLabel(status as EntityStatus)}
              size="small"
              sx={{
                ml: 1,
                backgroundColor: getStatusColor(status as EntityStatus),
                color: '#fff',
              }}
            />
          </Box>

          <Typography variant="body2" color="text.secondary">
            {entity.title} {entity.district_name ? `(${entity.district_name})` : ''}
          </Typography>
        </Box>

        <IconButton
          edge="end"
          onClick={e => {
            e.stopPropagation();
            handleToggle();
          }}
          sx={{ padding: 1 }}
          aria-expanded={expanded}
          aria-label="show more"
        >
          {expanded ? <KeyboardArrowUpIcon /> : <KeyboardArrowDownIcon />}
        </IconButton>
      </Box>

      {/* Expandable content */}
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box sx={{ px: 2, pb: 2 }}>
          {/* Notes section */}
          {notes && (
            <Box
              sx={{
                my: 1,
                p: 1.5,
                backgroundColor: 'rgba(0,0,0,0.03)',
                borderRadius: 1,
              }}
            >
              <Typography variant="body2">{notes}</Typography>
            </Box>
          )}

          {/* Contact information section */}
          <Box sx={{ mt: 2 }}>
            <EntityContactInfo entity={entity} />
          </Box>

          {/* Entity Details button */}
          <Box display="flex" justifyContent="flex-end" mt={2}>
            <Button
              variant="contained"
              size="small"
              color="primary"
              onClick={() => navigate(`/representatives/${entity.id}`)}
            >
              View Representative Details
            </Button>
          </Box>
        </Box>
      </Collapse>
    </Box>
  );
};

interface UserEntityProjectSectionProps {
  project: Project;
  statusRecords: EntityStatusRecord[];
  representativeTitle?: string;
}

const UserEntityProjectSection: React.FC<UserEntityProjectSectionProps> = ({
  project,
  statusRecords,
  representativeTitle = 'Representative',
}) => {
  const navigate = useNavigate();
  const { userRepresentatives, hasUserRepresentatives } = useUserRepresentatives();

  // Filter entities that match the project jurisdiction
  const relevantEntities = userRepresentatives.filter(
    entity => entity.jurisdiction_id === project.jurisdiction_id
  );

  // Create a map of entity ID to status record for quick lookups
  const statusMap = statusRecords.reduce(
    (acc, record) => {
      acc[record.entity_id] = record;
      return acc;
    },
    {} as Record<string, EntityStatusRecord>
  );

  if (!hasUserRepresentatives) {
    return (
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          Your {representativeTitle}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Find your {representativeTitle.toLowerCase()} to see where they stand on this project.
        </Typography>
        <Button
          variant="outlined"
          color="primary"
          size="small"
          onClick={() => navigate('/representatives')}
          sx={{ mt: 2 }}
        >
          Find Your {representativeTitle}
        </Button>
      </Paper>
    );
  }

  if (relevantEntities.length === 0) {
    return (
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" gutterBottom>
          Your {representativeTitle}
        </Typography>
        <Typography variant="body2" color="textSecondary">
          Your saved{' '}
          {userRepresentatives?.length > 1
            ? representativeTitle.toLowerCase() + 's are '
            : representativeTitle.toLowerCase()}
          {' is '}
          not involved with this project.
        </Typography>
        <Button
          variant="outlined"
          color="primary"
          size="small"
          onClick={() => navigate('/representatives')}
          sx={{ mt: 2 }}
        >
          Find More Representatives
        </Button>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
      <Typography variant="h6" gutterBottom>
        {relevantEntities?.length == 1
          ? `Where Your ${representativeTitle} Stands`
          : `Where Your ${representativeTitle}s Stand`}
      </Typography>

      <List disablePadding sx={{ mt: 2 }}>
        {relevantEntities.map(entity => (
          <RepresentativeItem
            key={entity.id}
            entity={entity}
            statusRecord={statusMap[entity.id]}
            statusLabels={project.dashboard_config?.status_labels}
          />
        ))}
      </List>

      {relevantEntities.length > 1 && (
        <Button
          variant="outlined"
          fullWidth
          onClick={() => navigate(`/contact?project=${project.id}`)}
          sx={{ mt: 1 }}
        >
          Contact All Your {representativeTitle}s
        </Button>
      )}
    </Paper>
  );
};

export default UserEntityProjectSection;
