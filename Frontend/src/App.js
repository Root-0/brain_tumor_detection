import React from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import theme from './theme';
import BrainTumorDetection from './brain-tumor-detection';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <BrainTumorDetection />
    </ThemeProvider>
  );
}

export default App;
