import { createTheme } from '@mui/material/styles';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#6f42c1', // Custom purple for branding
    },
    secondary: {
      main: '#00bcd4', // Teal accent
    },
    background: {
      default: '#181A20',
      paper: '#23263A',
    },
    error: {
      main: '#e53935',
    },
    warning: {
      main: '#fbc02d',
    },
    success: {
      main: '#43a047',
    },
    info: {
      main: '#00bcd4',
    },
  },
  typography: {
    fontFamily: 'Poppins, Roboto, Arial, sans-serif',
    fontWeightBold: 700,
    h1: {
      fontWeight: 800,
      letterSpacing: '-2px',
    },
    h2: {
      fontWeight: 700,
      letterSpacing: '-1px',
    },
    button: {
      textTransform: 'none',
      fontWeight: 600,
    },
  },
  shape: {
    borderRadius: 12,
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 8px 32px 0 rgba(31, 38, 135, 0.15)',
          border: '1px solid #2e2e38',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          borderRadius: 8,
        },
      },
    },
  },
});

export default theme;
