import React from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  useTheme,
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
  const theme = useTheme();
  const { currentTheme, setTheme } = useCustomTheme();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  const toggleTheme = () => {
    setTheme(currentTheme.name === 'light' ? darkTheme : lightTheme);
  };

  return (
    <AppBar
      position="static"
      elevation={0}
      sx={{
        backgroundColor: theme.palette.background.paper,
        borderBottom: `1px solid ${theme.palette.divider}`,
      }}
    >
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
                  '& .logo-icon': {
                    color: theme.palette.primary.dark,
                  },
                  '& .logo-text': {
                    color: theme.palette.primary.main,
                  },
                },
              }}
            >
              <VolunteerActivismIcon
                className="logo-icon"
                sx={{
                  mr: 1.5,
                  color: theme.palette.primary.main,
                  fontSize: 28,
                  transition: 'color 0.2s ease',
                }}
              />
              <Typography
                className="logo-text"
                variant="h6"
                sx={{
                  color: theme.palette.text.primary,
                  textDecoration: 'none',
                  fontWeight: 700,
                  letterSpacing: '0.5px',
                  fontSize: { xs: '0.7rem' },
                  transition: 'color 0.2s ease',
                }}
              >
                {appConfig.name}
              </Typography>
            </Box>

            {/* Representative badge with popover - only show if screen is large enough */}
            <Box sx={{ display: { xs: 'none', sm: 'none', md: 'block' } }}>
              <RepresentativeBadge />
            </Box>
          </Box>

          <Box
            sx={{
              flexGrow: 1,
              display: { xs: 'none', sm: 'flex' }, // Hide on mobile
              justifyContent: 'center',
            }}
          >
            <>
              <Button
                color="inherit"
                component={RouterLink}
                to="/"
                sx={{
                  mx: 1,
                  color: isActive('/') ? theme.palette.primary.main : theme.palette.text.primary,
                  fontWeight: isActive('/') ? 700 : 500,
                  '&:hover': {
                    backgroundColor: 'rgba(25, 118, 210, 0.04)',
                  },
                }}
              >
                Home
              </Button>
              <Button
                color="inherit"
                component={RouterLink}
                to="/projects"
                sx={{
                  mx: 1,
                  color: isActive('/projects')
                    ? theme.palette.primary.main
                    : theme.palette.text.primary,
                  fontWeight: isActive('/projects') ? 700 : 500,
                  '&:hover': {
                    backgroundColor: 'rgba(25, 118, 210, 0.04)',
                  },
                }}
              >
                Projects
              </Button>
              <Button
                color="inherit"
                component={RouterLink}
                to="/representatives"
                sx={{
                  mx: 1,
                  color: isActive('/representatives')
                    ? theme.palette.primary.main
                    : theme.palette.text.primary,
                  fontWeight: isActive('/representatives') ? 700 : 500,
                  '&:hover': {
                    backgroundColor: 'rgba(25, 118, 210, 0.04)',
                  },
                }}
              >
                Find Representatives
              </Button>
            </>
          </Box>

          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <IconButton
              onClick={toggleTheme}
              color="inherit"
              sx={{
                color: theme.palette.text.primary,
                mr: 1,
              }}
              aria-label={
                currentTheme.name === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'
              }
            >
              {currentTheme.name === 'dark' ? <Brightness7Icon /> : <Brightness4Icon />}
            </IconButton>

            <UserMenu />
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header;
