import React, { createContext, useState, useContext, useMemo, ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider, createTheme } from '@mui/material';
import { ThemeConfig, lightTheme } from './themes';
import CssBaseline from '@mui/material/CssBaseline';

interface ThemeContextProps {
  currentTheme: ThemeConfig;
  setTheme: (theme: ThemeConfig) => void;
}

const ThemeContext = createContext<ThemeContextProps>({
  currentTheme: lightTheme,
  setTheme: () => {},
});

// eslint-disable-next-line react-refresh/only-export-components
export const useTheme = () => useContext(ThemeContext);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [currentTheme, setCurrentTheme] = useState<ThemeConfig>(lightTheme);

  const theme = useMemo(() => {
    return createTheme({
      palette: currentTheme.palette,
      typography: {
        fontFamily: currentTheme.fontFamily,
        h1: {
          fontWeight: 600,
        },
        h2: {
          fontWeight: 600,
        },
        h3: {
          fontWeight: 600,
        },
        h4: {
          fontWeight: 600,
        },
        h5: {
          fontWeight: 600,
        },
        h6: {
          fontWeight: 600,
        },
      },
      shape: {
        borderRadius: currentTheme.borderRadius,
      },
    });
  }, [currentTheme]);

  const contextValue = useMemo(() => {
    return {
      currentTheme,
      setTheme: setCurrentTheme,
    };
  }, [currentTheme]);

  // Overrides some of the mui components to improve styling on smaller screens
  const completeTheme = useMemo(() => {
    return createTheme({
      ...theme,
      components: {
        MuiCard: {
          styleOverrides: {
            root: {
              boxShadow: '0 4px 12px 0 rgba(0,0,0,0.05)',
              borderRadius: currentTheme.borderRadius,
            },
          },
        },
        MuiButton: {
          styleOverrides: {
            root: {
              textTransform: 'none',
              fontWeight: 600,
              borderRadius: currentTheme.borderRadius,
            },
          },
        },
        MuiChip: {
          styleOverrides: {
            root: {
              fontWeight: 500,
            },
          },
        },
        MuiContainer: {
          styleOverrides: {
            root: {
              [theme.breakpoints.down('sm')]: {
                padding: '0 12px',
              },
            },
          },
        },
        MuiPaper: {
          styleOverrides: {
            root: {
              [theme.breakpoints.down('sm')]: {
                padding: '12px',
              },
            },
          },
        },
        MuiTypography: {
          styleOverrides: {
            h3: {
              [theme.breakpoints.down('sm')]: {
                fontSize: '1.75rem',
              },
            },
            h5: {
              [theme.breakpoints.down('sm')]: {
                fontSize: '1.25rem',
              },
            },
          },
        },
      },
    });
  }, [theme, currentTheme]);

  return (
    <ThemeContext.Provider value={contextValue}>
      <MuiThemeProvider theme={completeTheme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};
