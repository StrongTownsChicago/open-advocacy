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
      main: '#1B5E38', // Deep civic forest green
      light: '#2E7D52',
      dark: '#0D3D21',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#D97706', // Warm amber — action, urgency, Chicago energy
      light: '#F59E0B',
      dark: '#B45309',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#F9F8F5', // Warm off-white — slightly papery, not clinical
      paper: '#FFFFFF',
    },
    text: {
      primary: '#1A1917', // Warm near-black
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
      main: '#3D7A5C', // Deep forest green
      light: '#5A9E7D',
      dark: '#285C43',
      contrastText: '#FFFFFF',
    },
    secondary: {
      main: '#D4915A', // Muted amber-terracotta
      light: '#E8B48A',
      dark: '#B8733C',
      contrastText: '#FFFFFF',
    },
    background: {
      default: '#0F1613', // Very dark green-tinted background
      paper: '#182119', // Dark green-tinted paper
    },
    text: {
      primary: '#F0EDE8',
      secondary: '#A3A09A',
    },
    divider: '#2A3328',
    success: {
      main: '#4E9E72',
      light: '#72B893',
      dark: '#357A56',
    },
    warning: {
      main: '#D4915A',
      light: '#E8B48A',
      dark: '#B8733C',
    },
  },
  borderRadius: 10,
  fontFamily: '"Plus Jakarta Sans", "Helvetica Neue", "Arial", sans-serif',
};

export const availableThemes = [lightTheme, darkTheme];
