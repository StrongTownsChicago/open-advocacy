import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  IconButton,
  Drawer,
  List,
  ListItem,
  Divider,
} from '@mui/material';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import GitHubIcon from '@mui/icons-material/GitHub';
import MenuIcon from '@mui/icons-material/Menu';
import CloseIcon from '@mui/icons-material/Close';
import VolunteerActivismIcon from '@mui/icons-material/VolunteerActivism';
import { useTheme as useCustomTheme } from '../../theme/ThemeProvider';
import { lightTheme, darkTheme } from '../../theme/themes';
import { appConfig } from '@/utils/config';
import RepresentativeBadge from './RepresentativeBadge';
import UserMenu from './UserMenu';

const NAV_LINKS = [
  { path: '/' as const, label: 'Home' },
  { path: '/projects' as const, label: 'Projects' },
  { path: '/representatives' as const, label: 'Find Representatives' },
  { path: '/scorecard' as const, label: 'Scorecard' },
];

const Header: React.FC = () => {
  const { currentTheme, setTheme } = useCustomTheme();
  const location = useLocation();
  const navigate = useNavigate();
  const [drawerOpen, setDrawerOpen] = useState(false);

  const isActive = (path: string) => location.pathname === path;

  const toggleTheme = () => {
    setTheme(currentTheme.name === 'light' ? darkTheme : lightTheme);
  };

  const isLight = currentTheme.name === 'light';

  const handleNavClick = (path: string) => {
    setDrawerOpen(false);
    navigate(path);
  };

  return (
    <>
      <AppBar position="static" elevation={0}>
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ height: 56 }}>
            {/* Left: logo + badge */}
            <Box sx={{ display: 'flex', flex: 1, alignItems: 'center' }}>
              <Box
                component={RouterLink}
                to="/"
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  textDecoration: 'none',
                  '&:hover': {
                    '& .logo-icon': { opacity: 0.85 },
                    '& .logo-text': { opacity: 0.85 },
                  },
                }}
              >
                <VolunteerActivismIcon
                  className="logo-icon"
                  sx={{
                    mr: 1.5,
                    color: 'rgba(255,255,255,0.9)',
                    fontSize: 26,
                    transition: 'opacity 0.2s ease',
                  }}
                />
                <Typography
                  className="logo-text"
                  variant="h6"
                  sx={{
                    color: '#FFFFFF',
                    textDecoration: 'none',
                    fontWeight: 700,
                    fontFamily: '"Fraunces", Georgia, serif',
                    letterSpacing: '0.3px',
                    fontSize: { xs: '0.9rem', sm: '1rem' },
                    transition: 'opacity 0.2s ease',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {appConfig.name}
                </Typography>
              </Box>

              <Box sx={{ display: { xs: 'none', md: 'block' }, ml: 2 }}>
                <RepresentativeBadge />
              </Box>
            </Box>

            {/* Center: desktop nav */}
            <Box sx={{ display: { xs: 'none', sm: 'flex' }, justifyContent: 'center' }}>
              {NAV_LINKS.map(({ path, label }) => (
                <Button
                  key={path}
                  color="inherit"
                  component={RouterLink}
                  to={path}
                  sx={{
                    mx: 0.5,
                    px: 2,
                    py: 1,
                    color: isActive(path) ? '#FFFFFF' : 'rgba(255,255,255,0.72)',
                    fontWeight: isActive(path) ? 700 : 500,
                    fontSize: '0.875rem',
                    position: 'relative',
                    borderRadius: '6px',
                    '&::after': isActive(path)
                      ? {
                          content: '""',
                          position: 'absolute',
                          bottom: 2,
                          left: '50%',
                          transform: 'translateX(-50%)',
                          width: '20px',
                          height: '2px',
                          backgroundColor: 'rgba(255,255,255,0.8)',
                          borderRadius: '1px',
                        }
                      : {},
                    '&:hover': {
                      backgroundColor: 'rgba(255,255,255,0.1)',
                      color: '#FFFFFF',
                    },
                  }}
                >
                  {label}
                </Button>
              ))}
            </Box>

            {/* Right: icons + user menu (desktop) / hamburger (mobile) */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, flex: 1, justifyContent: 'flex-end' }}>
              <IconButton
                component="a"
                href="https://github.com/StrongTownsChicago/open-advocacy"
                target="_blank"
                rel="noopener noreferrer"
                sx={{
                  color: 'rgba(255,255,255,0.8)',
                  width: 36,
                  height: 36,
                  '&:hover': { color: '#FFFFFF', backgroundColor: 'rgba(255,255,255,0.1)' },
                }}
                aria-label="View source on GitHub"
              >
                <GitHubIcon sx={{ fontSize: 20 }} />
              </IconButton>

              <IconButton
                onClick={toggleTheme}
                sx={{
                  color: 'rgba(255,255,255,0.8)',
                  width: 36,
                  height: 36,
                  '&:hover': { color: '#FFFFFF', backgroundColor: 'rgba(255,255,255,0.1)' },
                }}
                aria-label={isLight ? 'Switch to dark mode' : 'Switch to light mode'}
              >
                {isLight ? (
                  <Brightness4Icon sx={{ fontSize: 20 }} />
                ) : (
                  <Brightness7Icon sx={{ fontSize: 20 }} />
                )}
              </IconButton>

              {/* Desktop: user menu */}
              <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
                <UserMenu />
              </Box>

              {/* Mobile: hamburger */}
              <IconButton
                onClick={() => setDrawerOpen(true)}
                sx={{
                  display: { xs: 'flex', sm: 'none' },
                  color: 'rgba(255,255,255,0.8)',
                  width: 36,
                  height: 36,
                  '&:hover': { color: '#FFFFFF', backgroundColor: 'rgba(255,255,255,0.1)' },
                }}
                aria-label="Open menu"
              >
                <MenuIcon sx={{ fontSize: 22 }} />
              </IconButton>
            </Box>
          </Toolbar>
        </Container>
      </AppBar>

      {/* Mobile drawer */}
      <Drawer
        anchor="right"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        sx={{ display: { xs: 'block', sm: 'none' } }}
        PaperProps={{
          sx: { width: 260 },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', px: 2, py: 1.5 }}>
          <Typography variant="subtitle1" sx={{ fontWeight: 700, fontFamily: '"Fraunces", Georgia, serif' }}>
            {appConfig.name}
          </Typography>
          <IconButton onClick={() => setDrawerOpen(false)} size="small" aria-label="Close menu">
            <CloseIcon />
          </IconButton>
        </Box>

        <Divider />

        <List disablePadding>
          {NAV_LINKS.map(({ path, label }) => (
            <ListItem key={path} disablePadding>
              <Button
                fullWidth
                onClick={() => handleNavClick(path)}
                sx={{
                  justifyContent: 'flex-start',
                  px: 2,
                  py: 1.5,
                  borderRadius: 0,
                  fontWeight: isActive(path) ? 700 : 400,
                  color: isActive(path) ? 'primary.main' : 'text.primary',
                  backgroundColor: isActive(path) ? 'action.selected' : 'transparent',
                }}
              >
                {label}
              </Button>
            </ListItem>
          ))}
        </List>

        <Divider />

        <Box sx={{ px: 2, py: 2 }}>
          <UserMenu />
        </Box>
      </Drawer>
    </>
  );
};

export default Header;
