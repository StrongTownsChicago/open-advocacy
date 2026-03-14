import { PaletteOptions } from '@mui/material';

export interface ThemeConfig {
  name: string;
  palette: PaletteOptions;
  borderRadius: number;
  fontFamily: string;
}

export const lightTheme: ThemeConfig = {
  name: 'light',
  palette: {
    mode: 'light',
    primary: {
      main: '#1B5E38',    // Deep civic forest green
      light: '#2E7D52',
      dark: '#0D3D21',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#D97706',    // Warm amber — action, urgency, Chicago energy
      light: '#F59E0B',
      dark: '#B45309',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F9F8F5', // Warm off-white — slightly papery, not clinical
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1A1917',   // Warm near-black
      secondary: '#6B6560', // Warm medium gray
    },
    divider: '#E5E3DF',
    success: {
      main: '#166534',
      light: '#22C55E',
      dark: '#14532D',
    },
    warning: {
      main: '#D97706',
      light: '#F59E0B',
      dark: '#B45309',
    },
    error: {
      main: '#DC2626',
      light: '#F87171',
      dark: '#991B1B',
    },
  },
  borderRadius: 10,
  fontFamily: '"Plus Jakarta Sans", "Helvetica Neue", "Arial", sans-serif',
};

export const darkTheme: ThemeConfig = {
  name: 'dark',
  palette: {
    mode: 'dark',
    primary: {
      main: '#4ADE80',    // Bright civic green for dark mode
      light: '#86EFAC',
      dark: '#22C55E',
      contrastText: '#052E16',
    },
    secondary: {
      main: '#F59E0B',    // Warm amber
      light: '#FCD34D',
      dark: '#D97706',
      contrastText: '#1C0A00',
    },
    background: {
      default: '#0F1613',  // Very dark green-tinted background
      paper: '#182119',    // Dark green-tinted paper
    },
    text: {
      primary: '#F0EDE8',
      secondary: '#A3A09A',
    },
    divider: '#2A3328',
    success: {
      main: '#4ADE80',
      light: '#86EFAC',
      dark: '#22C55E',
    },
    warning: {
      main: '#F59E0B',
      light: '#FCD34D',
      dark: '#D97706',
    },
  },
  borderRadius: 10,
  fontFamily: '"Plus Jakarta Sans", "Helvetica Neue", "Arial", sans-serif',
};

export const availableThemes = [lightTheme, darkTheme];
