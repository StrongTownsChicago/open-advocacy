import React, { useState } from 'react';
import {
  Box,
  Button,
  ButtonBase,
  Chip,
  Avatar,
  Divider,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Paper,
  Popover,
  Tooltip,
  Typography,
} from '@mui/material';
import { Link as RouterLink } from 'react-router-dom';
import PersonIcon from '@mui/icons-material/Person';
import PlaceIcon from '@mui/icons-material/Place';
import ArrowForwardIcon from '@mui/icons-material/ArrowForward';
import { useTheme } from '@mui/material/styles';
import { useUserRepresentatives } from '../../contexts/UserRepresentativesContext';
import { useNavigate } from 'react-router-dom';

const RepresentativeBadge: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { hasUserRepresentatives, userRepresentatives, userAddress } = useUserRepresentatives();
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  if (!hasUserRepresentatives) return null;

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleEntityClick = (entityId: string) => {
    navigate(`/representatives/${entityId}`);
    handleClose();
  };

  const open = Boolean(anchorEl);

  return (
    <>
      <Tooltip title={`Your representatives for: ${userAddress}`}>
        <Chip
          icon={<PersonIcon />}
          label={`${userRepresentatives.length} Saved Representative${userRepresentatives.length > 1 ? 's' : ''}`}
          color="primary"
          variant="outlined"
          onClick={handleClick}
          sx={{
            ml: 2,
            cursor: 'pointer',
            '&:hover': {
              backgroundColor: theme.palette.primary.main + '1A', // 10% opacity
            },
          }}
        />
      </Tooltip>

      <Popover
        open={open}
        anchorEl={anchorEl}
        onClose={handleClose}
        anchorOrigin={{
          vertical: 'bottom',
          horizontal: 'center',
        }}
        transformOrigin={{
          vertical: 'top',
          horizontal: 'center',
        }}
      >
        <Paper sx={{ width: 320, maxHeight: 400, overflow: 'auto' }}>
          <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
            <Typography variant="subtitle1" fontWeight="bold">
              Your Representatives
            </Typography>
            <Typography variant="caption" color="text.secondary">
              Based on: {userAddress}
            </Typography>
          </Box>

          <List dense>
            {userRepresentatives.map(rep => (
              <ListItem
                key={rep.id}
                component={ButtonBase}
                onClick={() => handleEntityClick(rep.id)}
                sx={{
                  width: '100%',
                  textAlign: 'left',
                  padding: '8px 16px',
                  '&:hover': {
                    backgroundColor: theme.palette.action.hover,
                  },
                }}
              >
                <ListItemIcon sx={{ minWidth: 36 }}>
                  {rep.image_url ? (
                    <Avatar
                      src={rep.image_url}
                      sx={{
                        width: 24,
                        height: 24,
                      }}
                    >
                      <PersonIcon fontSize="small" />
                    </Avatar>
                  ) : (
                    <PersonIcon color="primary" fontSize="small" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="body2" component="span">
                      <strong>{rep.name}</strong>
                    </Typography>
                  }
                  secondary={
                    <Typography component="span" variant="caption">
                      <Box
                        component="span"
                        sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                      >
                        <PlaceIcon sx={{ fontSize: 14 }} />
                        <span>{rep.district_name || rep.title || 'Representative'}</span>
                      </Box>
                    </Typography>
                  }
                />
                <ArrowForwardIcon fontSize="small" color="action" sx={{ opacity: 0.6 }} />
              </ListItem>
            ))}
          </List>

          <Divider />

          <Box sx={{ p: 1.5, textAlign: 'center' }}>
            <Button
              size="small"
              variant="outlined"
              component={RouterLink}
              to="/representatives"
              onClick={handleClose}
            >
              View All Representatives
            </Button>
          </Box>
        </Paper>
      </Popover>
    </>
  );
};

export default RepresentativeBadge;
