import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  IconButton,
} from '@mui/material';
import { Link as RouterLink, useLocation } from 'react-router-dom';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import VolunteerActivismIcon from '@mui/icons-material/VolunteerActivism';
import { useTheme as useCustomTheme } from '../../theme/ThemeProvider';
import { lightTheme, darkTheme } from '../../theme/themes';
import { appConfig } from '@/utils/config';
import RepresentativeBadge from './RepresentativeBadge';
import UserMenu from './UserMenu';

const Header: React.FC = () => {
  const { currentTheme, setTheme } = useCustomTheme();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const toggleTheme = () => {
    setTheme(currentTheme.name === 'light' ? darkTheme : lightTheme);
  };

  const isLight = currentTheme.name === 'light';

  return (
    <AppBar position="static" elevation={0}>
      <Container maxWidth="lg">
        <Toolbar
          disableGutters
          sx={{
            height: { xs: 56, sm: 64 },
            flexDirection: { xs: 'column', sm: 'row' },
          }}
        >
          <Box
            sx={{
              display: 'flex',
              width: { xs: '100%', sm: 'auto' },
              justifyContent: { xs: 'space-between', sm: 'flex-start' },
              alignItems: 'center',
            }}
          >
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
                }}
              >
                {appConfig.name}
              </Typography>
            </Box>

            <Box sx={{ display: { xs: 'none', sm: 'none', md: 'block' }, ml: 2 }}>
              <RepresentativeBadge />
            </Box>
          </Box>

          <Box
            sx={{
              flexGrow: 1,
              display: { xs: 'none', sm: 'flex' },
              justifyContent: 'center',
            }}
          >
            {(['/', '/projects', '/representatives', '/scorecard'] as const).map((path, i) => {
              const labels = ['Home', 'Projects', 'Find Representatives', 'Scorecard'];
              return (
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
                  {labels[i]}
                </Button>
              );
            })}
          </Box>

          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
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

            <UserMenu />
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header;
