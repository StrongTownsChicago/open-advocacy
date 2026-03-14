import React, { useState } from 'react';
import {
  Box,
  Button,
  Divider,
  IconButton,
  ListItemIcon,
  ListItemText,
  Menu,
  MenuItem,
  Tooltip,
  Typography,
} from '@mui/material';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import LoginIcon from '@mui/icons-material/Login';
import LogoutIcon from '@mui/icons-material/Logout';
import AccountCircleIcon from '@mui/icons-material/AccountCircle';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import SupervisorAccountIcon from '@mui/icons-material/SupervisorAccount';
import { useTheme } from '@mui/material/styles';
import { useAuth } from '../../contexts/AuthContext';

const UserMenu: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const { user, logout, isAuthenticated, hasAnyRole } = useAuth();
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const open = Boolean(anchorEl);

  const handleOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    logout();
    handleClose();
  };

  const handleLogin = () => {
    navigate('/login');
  };

  if (!isAuthenticated) {
    return (
      <Button
        variant="outlined"
        size="small"
        startIcon={<LoginIcon />}
        onClick={handleLogin}
        sx={{ ml: 1 }}
      >
        Sign In
      </Button>
    );
  }

  return (
    <>
      <Tooltip title="Account settings">
        <IconButton
          onClick={handleOpen}
          size="small"
          aria-controls={open ? 'account-menu' : undefined}
          aria-haspopup="true"
          aria-expanded={open ? 'true' : undefined}
          sx={{
            ml: 1,
            border: `1px solid ${theme.palette.divider}`,
            borderRadius: 2,
            padding: '4px 8px',
            '&:hover': {
              backgroundColor: theme.palette.action.hover,
            },
          }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <AccountCircleIcon sx={{ mr: 1 }} />
            <Typography
              variant="body2"
              sx={{ mr: 1, display: { xs: 'none', sm: 'block' } }}
            >
              {user?.name || user?.email || 'User'}
            </Typography>
          </Box>
        </IconButton>
      </Tooltip>

      <Menu
        anchorEl={anchorEl}
        id="account-menu"
        open={open}
        onClose={handleClose}
        transformOrigin={{ horizontal: 'right', vertical: 'top' }}
        anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
        PaperProps={{
          elevation: 3,
          sx: {
            minWidth: 200,
            mt: 1,
            '& .MuiMenuItem-root': {
              px: 2,
              py: 1,
            },
          },
        }}
      >
        <MenuItem onClick={handleClose} disabled>
          <ListItemIcon>
            <AccountCircleIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText
            primary={user?.name || 'User'}
            secondary={user?.email}
            primaryTypographyProps={{ variant: 'body2' }}
            secondaryTypographyProps={{ variant: 'caption' }}
          />
        </MenuItem>

        <Divider />

        {/* Admin menu item - only visible to admins */}
        {hasAnyRole(['super_admin', 'group_admin']) && (
          <MenuItem component={RouterLink} to="/admin" onClick={handleClose}>
            <ListItemIcon>
              <AdminPanelSettingsIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Admin User Management" />
          </MenuItem>
        )}

        {/* User management - only for admins */}
        {hasAnyRole(['super_admin', 'group_admin']) && (
          <MenuItem component={RouterLink} to="/register" onClick={handleClose}>
            <ListItemIcon>
              <SupervisorAccountIcon fontSize="small" />
            </ListItemIcon>
            <ListItemText primary="Add User" />
          </MenuItem>
        )}

        {/* Logout option */}
        <MenuItem onClick={handleLogout}>
          <ListItemIcon>
            <LogoutIcon fontSize="small" />
          </ListItemIcon>
          <ListItemText primary="Logout" />
        </MenuItem>
      </Menu>
    </>
  );
};

export default UserMenu;
