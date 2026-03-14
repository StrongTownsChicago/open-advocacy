import React, { createContext, useState, useContext, useMemo, ReactNode } from 'react';
import { ThemeProvider as MuiThemeProvider, createTheme, alpha } from '@mui/material';
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
        // Fraunces for display headings — editorial, authoritative
        h1: { fontWeight: 700, fontFamily: '"Fraunces", Georgia, serif', letterSpacing: '-0.02em' },
        h2: { fontWeight: 600, fontFamily: '"Fraunces", Georgia, serif', letterSpacing: '-0.01em' },
        h3: { fontWeight: 600, fontFamily: '"Fraunces", Georgia, serif', letterSpacing: '-0.01em' },
        h4: { fontWeight: 600, fontFamily: '"Fraunces", Georgia, serif' },
        h5: { fontWeight: 600 },
        h6: { fontWeight: 600 },
        subtitle1: { fontWeight: 500 },
        subtitle2: { fontWeight: 600, letterSpacing: '0.04em', textTransform: 'uppercase', fontSize: '0.7rem' },
        button: { fontWeight: 600, letterSpacing: '0.01em' },
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

  const completeTheme = useMemo(() => {
    const isLight = currentTheme.palette.mode === 'light';
    const primaryMain = (currentTheme.palette.primary as { main: string }).main;
    const bgDefault = (currentTheme.palette.background as { default: string }).default;

    return createTheme({
      ...theme,
      components: {
        MuiCssBaseline: {
          styleOverrides: {
            body: {
              backgroundColor: bgDefault,
            },
          },
        },
        MuiAppBar: {
          styleOverrides: {
            root: {
              backgroundColor: primaryMain,
              backgroundImage: 'none',
              boxShadow: isLight
                ? '0 1px 0 rgba(0,0,0,0.08), 0 2px 8px rgba(0,0,0,0.04)'
                : '0 1px 0 rgba(255,255,255,0.06)',
            },
          },
        },
        MuiCard: {
          styleOverrides: {
            root: {
              boxShadow: isLight
                ? '0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)'
                : '0 1px 3px rgba(0,0,0,0.4)',
              borderRadius: currentTheme.borderRadius,
              border: isLight ? '1px solid rgba(0,0,0,0.06)' : '1px solid rgba(255,255,255,0.06)',
            },
          },
        },
        MuiPaper: {
          styleOverrides: {
            root: {
              boxShadow: 'none',
              border: isLight ? '1px solid rgba(0,0,0,0.07)' : '1px solid rgba(255,255,255,0.06)',
              backgroundImage: 'none',
            },
            elevation1: {
              boxShadow: isLight
                ? '0 1px 3px rgba(0,0,0,0.06), 0 4px 16px rgba(0,0,0,0.04)'
                : '0 1px 3px rgba(0,0,0,0.4)',
            },
            elevation3: {
              boxShadow: isLight
                ? '0 2px 8px rgba(0,0,0,0.08), 0 8px 24px rgba(0,0,0,0.06)'
                : '0 2px 8px rgba(0,0,0,0.5)',
            },
          },
        },
        MuiButton: {
          styleOverrides: {
            root: {
              textTransform: 'none',
              fontWeight: 600,
              borderRadius: currentTheme.borderRadius,
              padding: '8px 20px',
            },
            contained: {
              boxShadow: 'none',
              '&:hover': {
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
              },
            },
            outlined: {
              borderWidth: '1.5px',
              '&:hover': {
                borderWidth: '1.5px',
              },
            },
          },
        },
        MuiChip: {
          styleOverrides: {
            root: {
              fontWeight: 600,
              fontSize: '0.75rem',
              borderRadius: 6,
            },
          },
        },
        MuiTableHead: {
          styleOverrides: {
            root: {
              '& .MuiTableCell-head': {
                fontWeight: 700,
                fontSize: '0.7rem',
                letterSpacing: '0.06em',
                textTransform: 'uppercase',
                color: isLight ? '#6B6560' : '#A3A09A',
                backgroundColor: isLight ? '#F9F8F5' : '#0F1613',
                borderBottom: isLight ? '2px solid #E5E3DF' : '2px solid #2A3328',
                padding: '12px 16px',
              },
            },
          },
        },
        MuiTableRow: {
          styleOverrides: {
            root: {
              '&:nth-of-type(even)': {
                backgroundColor: isLight
                  ? alpha(primaryMain, 0.02)
                  : 'rgba(255,255,255,0.02)',
              },
              '&:hover': {
                backgroundColor: isLight
                  ? `${alpha(primaryMain, 0.04)} !important`
                  : 'rgba(255,255,255,0.04) !important',
              },
            },
          },
        },
        MuiTableCell: {
          styleOverrides: {
            root: {
              borderColor: isLight ? '#F0EDE8' : '#2A3328',
              padding: '12px 16px',
            },
          },
        },
        MuiInputBase: {
          styleOverrides: {
            root: {
              borderRadius: `${currentTheme.borderRadius}px`,
            },
          },
        },
        MuiOutlinedInput: {
          styleOverrides: {
            root: {
              '& .MuiOutlinedInput-notchedOutline': {
                borderColor: isLight ? '#D6D3CE' : '#3A3F38',
              },
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
        MuiLinearProgress: {
          styleOverrides: {
            root: {
              borderRadius: 4,
              backgroundColor: isLight ? '#E5E3DF' : '#2A3328',
            },
          },
        },
        MuiDivider: {
          styleOverrides: {
            root: {
              borderColor: isLight ? '#E5E3DF' : '#2A3328',
            },
          },
        },
        MuiTooltip: {
          styleOverrides: {
            tooltip: {
              borderRadius: 6,
              fontSize: '0.75rem',
              fontFamily: currentTheme.fontFamily,
              padding: '6px 10px',
            },
          },
        },
        MuiTableSortLabel: {
          styleOverrides: {
            root: {
              fontSize: '0.7rem',
              fontWeight: 700,
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
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
