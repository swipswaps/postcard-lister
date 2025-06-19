import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Container,
  Paper,
  Box,
  Tabs,
  Tab,
  Chip,
  Alert
} from '@mui/material';
import {
  SolarPower,
  Terminal,
  CloudUpload,
  Analytics,
  Settings
} from '@mui/icons-material';

import VerbatimTerminal from './components/VerbatimTerminal';
import ProcessingControl from './components/ProcessingControl';
import StatusDashboard from './components/StatusDashboard';
import ResultsViewer from './components/ResultsViewer';

// Dark theme optimized for terminal output
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00ff00', // Terminal green
    },
    secondary: {
      main: '#ff9800', // Solar orange
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#00ff00',
      secondary: '#ffffff',
    },
  },
  typography: {
    fontFamily: '"Roboto Mono", "Courier New", monospace',
    h4: {
      fontWeight: 600,
    },
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid #333',
        },
      },
    },
  },
});

function TabPanel({ children, value, index, ...other }) {
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`tabpanel-${index}`}
      aria-labelledby={`tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

function App() {
  const [tabValue, setTabValue] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [terminalOutput, setTerminalOutput] = useState([]);
  const [processingStatus, setProcessingStatus] = useState('idle');

  // WebSocket connections
  const [terminalWs, setTerminalWs] = useState(null);
  const [apiWs, setApiWs] = useState(null);

  useEffect(() => {
    // Connect to terminal output stream
    const connectTerminal = () => {
      const ws = new WebSocket('ws://localhost:8081');
      
      ws.onopen = () => {
        console.log('🔧 Terminal WebSocket connected');
        setConnectionStatus('connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          setTerminalOutput(prev => [...prev, {
            ...message,
            id: Date.now() + Math.random()
          }]);
        } catch (e) {
          console.error('Failed to parse terminal message:', e);
        }
      };
      
      ws.onclose = () => {
        console.log('🔌 Terminal WebSocket disconnected');
        setConnectionStatus('disconnected');
        // Reconnect after 3 seconds
        setTimeout(connectTerminal, 3000);
      };
      
      ws.onerror = (error) => {
        console.error('Terminal WebSocket error:', error);
        setConnectionStatus('error');
      };
      
      setTerminalWs(ws);
    };

    // Connect to API control
    const connectAPI = () => {
      const ws = new WebSocket('ws://localhost:8081');
      
      ws.onopen = () => {
        console.log('🔌 API WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'process_started' || message.type === 'batch_started') {
            setProcessingStatus('running');
          } else if (message.type === 'process_complete') {
            setProcessingStatus('complete');
          } else if (message.type === 'error') {
            setProcessingStatus('error');
          }
        } catch (e) {
          console.error('Failed to parse API message:', e);
        }
      };
      
      ws.onclose = () => {
        console.log('🔌 API WebSocket disconnected');
        // Reconnect after 3 seconds
        setTimeout(connectAPI, 3000);
      };
      
      setApiWs(ws);
    };

    connectTerminal();
    connectAPI();

    // Cleanup on unmount
    return () => {
      if (terminalWs) terminalWs.close();
      if (apiWs) apiWs.close();
    };
  }, [terminalWs, apiWs]); // Added dependencies to fix React Hook warning

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'success';
      case 'error': return 'error';
      default: return 'warning';
    }
  };

  const getConnectionStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'error': return 'Error';
      default: return 'Connecting...';
    }
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <AppBar position="static" sx={{ bgcolor: '#1a1a1a' }}>
        <Toolbar>
          <SolarPower sx={{ mr: 2, color: '#ff9800' }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, color: '#ffffff' }}>
            🌞 Solar Panel Catalog System - Material UI
          </Typography>
          <Chip
            label={getConnectionStatusText()}
            color={getConnectionStatusColor()}
            size="small"
            sx={{ mr: 2 }}
          />
          <Chip
            label={`Processing: ${processingStatus}`}
            color={processingStatus === 'running' ? 'primary' : 'default'}
            size="small"
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="xl" sx={{ mt: 2 }}>
        {connectionStatus === 'disconnected' && (
          <Alert severity="warning" sx={{ mb: 2 }}>
            🔌 WebSocket disconnected. Make sure the WebSocket bridge is running:
            <code style={{ marginLeft: 8 }}>python3 websocket/server.py</code>
          </Alert>
        )}

        <Paper sx={{ width: '100%', bgcolor: '#1a1a1a' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="solar panel catalog tabs"
            sx={{
              borderBottom: 1,
              borderColor: 'divider',
              '& .MuiTab-root': { color: '#ffffff' },
              '& .Mui-selected': { color: '#00ff00 !important' }
            }}
          >
            <Tab
              icon={<Terminal />}
              label="Verbatim Terminal"
              id="tab-0"
              aria-controls="tabpanel-0"
            />
            <Tab
              icon={<CloudUpload />}
              label="Processing Control"
              id="tab-1"
              aria-controls="tabpanel-1"
            />
            <Tab
              icon={<Analytics />}
              label="Status Dashboard"
              id="tab-2"
              aria-controls="tabpanel-2"
            />
            <Tab
              icon={<Settings />}
              label="Results Viewer"
              id="tab-3"
              aria-controls="tabpanel-3"
            />
          </Tabs>

          <TabPanel value={tabValue} index={0}>
            <VerbatimTerminal 
              output={terminalOutput}
              connectionStatus={connectionStatus}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            <ProcessingControl 
              apiWs={apiWs}
              processingStatus={processingStatus}
              setProcessingStatus={setProcessingStatus}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <StatusDashboard 
              terminalOutput={terminalOutput}
              processingStatus={processingStatus}
            />
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <ResultsViewer 
              terminalOutput={terminalOutput}
            />
          </TabPanel>
        </Paper>
      </Container>
    </ThemeProvider>
  );
}

export default App;
