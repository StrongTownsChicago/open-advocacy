import React, { useState } from 'react';
import {
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
import LocationOnIcon from '@mui/icons-material/LocationOn';
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
  const isLight = theme.palette.mode === 'light';

  const getStatusLabel = makeStatusLabelFn(statusLabels);
  const status = statusRecord?.status || 'unknown';
  const notes = statusRecord?.notes;
  const statusColor = getStatusColor(status as EntityStatus);

  const handleToggle = () => {
    setExpanded(!expanded);
  };

  return (
    <Box
      sx={{
        mb: 1.5,
        borderRadius: 2,
        overflow: 'hidden',
        border: `1px solid ${isLight ? 'rgba(0,0,0,0.07)' : 'rgba(255,255,255,0.07)'}`,
        borderLeft: `3px solid ${statusColor}`,
        backgroundColor: isLight
          ? `${statusColor}06`
          : `${statusColor}10`,
        transition: 'all 0.15s ease',
        '&:hover': {
          backgroundColor: isLight ? `${statusColor}10` : `${statusColor}15`,
        },
      }}
    >
      <Box
        display="flex"
        alignItems="center"
        onClick={handleToggle}
        sx={{
          padding: '12px 16px',
          cursor: 'pointer',
        }}
      >
        <Avatar
          src={entity.image_url}
          sx={{
            mr: 1.5,
            width: 40,
            height: 40,
            bgcolor: statusColor,
            fontSize: '0.9rem',
            fontWeight: 700,
          }}
        >
          {entity.image_url ? null : <PersonIcon sx={{ fontSize: 20 }} />}
        </Avatar>

        <Box flexGrow={1} minWidth={0}>
          <Box display="flex" alignItems="center" gap={1} flexWrap="wrap" mb={0.25}>
            <Typography
              variant="body1"
              fontWeight="700"
              sx={{ fontFamily: '"Fraunces", Georgia, serif', fontSize: '1rem' }}
            >
              {entity.name}
            </Typography>
            <Chip
              label={getStatusLabel(status as EntityStatus)}
              size="small"
              sx={{
                backgroundColor: statusColor,
                color: '#fff',
                fontWeight: 600,
                fontSize: '0.7rem',
                height: 20,
                borderRadius: '4px',
              }}
            />
          </Box>

          <Typography variant="body2" color="text.secondary" sx={{ fontSize: '0.8rem' }}>
            {entity.title}
            {entity.district_name ? ` · ${entity.district_name}` : ''}
          </Typography>
        </Box>

        <IconButton
          edge="end"
          onClick={e => {
            e.stopPropagation();
            handleToggle();
          }}
          sx={{
            padding: 0.5,
            color: 'text.secondary',
            ml: 1,
          }}
          aria-expanded={expanded}
          aria-label="show more"
        >
          {expanded ? (
            <KeyboardArrowUpIcon sx={{ fontSize: 18 }} />
          ) : (
            <KeyboardArrowDownIcon sx={{ fontSize: 18 }} />
          )}
        </IconButton>
      </Box>

      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box
          sx={{
            px: 2,
            pb: 2,
            borderTop: `1px solid ${isLight ? 'rgba(0,0,0,0.06)' : 'rgba(255,255,255,0.06)'}`,
            pt: 1.5,
          }}
        >
          {notes && (
            <Box
              sx={{
                mb: 1.5,
                p: 1.5,
                backgroundColor: isLight ? 'rgba(0,0,0,0.03)' : 'rgba(255,255,255,0.04)',
                borderRadius: 1.5,
                borderLeft: `2px solid ${statusColor}`,
              }}
            >
              <Typography variant="body2" sx={{ fontSize: '0.85rem', fontStyle: 'italic' }}>
                "{notes}"
              </Typography>
            </Box>
          )}

          <Box sx={{ mt: 1 }}>
            <EntityContactInfo entity={entity} />
          </Box>

          <Box display="flex" justifyContent="flex-end" mt={1.5}>
            <Button
              variant="outlined"
              size="small"
              color="primary"
              onClick={() => navigate(`/representatives/${entity.id}`)}
              sx={{ fontSize: '0.8rem' }}
            >
              View Details
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
  const theme = useTheme();
  const isLight = theme.palette.mode === 'light';
  const primaryColor = theme.palette.primary.main;

  const relevantEntities = userRepresentatives.filter(
    entity => entity.jurisdiction_id === project.jurisdiction_id
  );

  const statusMap = statusRecords.reduce(
    (acc, record) => {
      acc[record.entity_id] = record;
      return acc;
    },
    {} as Record<string, EntityStatusRecord>
  );

  if (!hasUserRepresentatives) {
    return (
      <Box
        sx={{
          p: 3,
          mb: 3,
          borderRadius: 2,
          background: isLight
            ? `linear-gradient(135deg, ${primaryColor}08 0%, ${primaryColor}04 100%)`
            : `linear-gradient(135deg, ${primaryColor}18 0%, ${primaryColor}08 100%)`,
          border: `1px solid ${primaryColor}20`,
          borderLeft: `4px solid ${primaryColor}`,
          display: 'flex',
          alignItems: 'flex-start',
          gap: 2,
        }}
      >
        <Box
          sx={{
            width: 48,
            height: 48,
            borderRadius: '12px',
            backgroundColor: `${primaryColor}15`,
            border: `1px solid ${primaryColor}25`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            mt: 0.25,
          }}
        >
          <LocationOnIcon sx={{ color: primaryColor, fontSize: 24 }} />
        </Box>

        <Box flexGrow={1}>
          <Typography
            variant="h6"
            sx={{
              fontFamily: '"Fraunces", Georgia, serif',
              fontWeight: 600,
              mb: 0.5,
              fontSize: '1.05rem',
              color: 'text.primary',
            }}
          >
            Your {representativeTitle}
          </Typography>
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{ mb: 1.5, fontSize: '0.875rem', lineHeight: 1.5 }}
          >
            Find your {representativeTitle.toLowerCase()} to see where they stand on this project.
          </Typography>
          <Button
            variant="contained"
            color="primary"
            size="small"
            onClick={() => navigate('/representatives')}
            sx={{ fontWeight: 600, fontSize: '0.8rem' }}
          >
            Find Your {representativeTitle}
          </Button>
        </Box>
      </Box>
    );
  }

  if (relevantEntities.length === 0) {
    return (
      <Box
        sx={{
          p: 3,
          mb: 3,
          borderRadius: 2,
          backgroundColor: isLight ? 'rgba(0,0,0,0.02)' : 'rgba(255,255,255,0.03)',
          border: `1px solid ${isLight ? 'rgba(0,0,0,0.07)' : 'rgba(255,255,255,0.07)'}`,
        }}
      >
        <Typography variant="h6" gutterBottom sx={{ fontFamily: '"Fraunces", Georgia, serif', fontSize: '1.05rem' }}>
          Your {representativeTitle}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1.5 }}>
          Your saved{' '}
          {userRepresentatives?.length > 1
            ? representativeTitle.toLowerCase() + 's are '
            : representativeTitle.toLowerCase() + ' is '}
          not involved with this project.
        </Typography>
        <Button
          variant="outlined"
          color="primary"
          size="small"
          onClick={() => navigate('/representatives')}
          sx={{ fontWeight: 600, fontSize: '0.8rem' }}
        >
          Find More Representatives
        </Button>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        p: 3,
        mb: 3,
        borderRadius: 2,
        background: isLight
          ? `linear-gradient(135deg, ${primaryColor}06 0%, ${primaryColor}02 100%)`
          : `linear-gradient(135deg, ${primaryColor}15 0%, ${primaryColor}06 100%)`,
        border: `1px solid ${primaryColor}18`,
        borderLeft: `4px solid ${primaryColor}`,
      }}
    >
      <Typography
        variant="h6"
        gutterBottom
        sx={{
          fontFamily: '"Fraunces", Georgia, serif',
          fontWeight: 600,
          fontSize: '1.05rem',
          mb: 2,
        }}
      >
        {relevantEntities?.length === 1
          ? `Where Your ${representativeTitle} Stands`
          : `Where Your ${representativeTitle}s Stand`}
      </Typography>

      <List disablePadding>
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
          color="primary"
          fullWidth
          onClick={() => navigate(`/contact?project=${project.id}`)}
          sx={{ mt: 1.5, fontWeight: 600, fontSize: '0.85rem' }}
        >
          Contact All Your {representativeTitle}s
        </Button>
      )}
    </Box>
  );
};

export default UserEntityProjectSection;
