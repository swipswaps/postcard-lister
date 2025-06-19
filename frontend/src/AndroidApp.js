import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  Fab,
  AppBar,
  Toolbar,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  LinearProgress,
  Alert,
  Snackbar
} from '@mui/material';
import {
  Menu as MenuIcon,
  PhotoCamera,
  CloudUpload,
  Settings,
  Home,
  Folder,
  GitHub,
  PlayArrow,
  CheckCircle,
  Error as ErrorIcon
} from '@mui/icons-material';

const AndroidApp = () => {
  // State management
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentView, setCurrentView] = useState('home');
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [verbatimLog, setVerbatimLog] = useState([]);
  const [websocket, setWebsocket] = useState(null);
  
  // Form state
  const [inputFile, setInputFile] = useState('');
  const [outputDir, setOutputDir] = useState('catalog/');
  const [autoUpload, setAutoUpload] = useState(true);
  const [verboseMode, setVerboseMode] = useState(true);

  // WebSocket connection - FIXED to prevent re-render loops
  useEffect(() => {
    let ws = null;
    let reconnectTimeout = null;
    let isConnecting = false;

    const connectWebSocket = () => {
      if (isConnecting) return;
      isConnecting = true;

      try {
        ws = new WebSocket('ws://localhost:8081');

        ws.onopen = () => {
          isConnecting = false;
          setConnectionStatus('connected');
          setWebsocket(ws);
          console.log('WebSocket connected');

          // Request verbatim log
          ws.send(JSON.stringify({ type: 'get_verbatim_log' }));
        };

        ws.onclose = () => {
          isConnecting = false;
          setConnectionStatus('disconnected');
          setWebsocket(null);
          console.log('WebSocket disconnected');

          // Auto-reconnect after 5 seconds (longer delay to prevent loops)
          if (!reconnectTimeout) {
            reconnectTimeout = setTimeout(() => {
              reconnectTimeout = null;
              connectWebSocket();
            }, 5000);
          }
        };

        ws.onerror = (error) => {
          isConnecting = false;
          setConnectionStatus('error');
          console.error('WebSocket error:', error);
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);

            // Update verbatim log if present
            if (data.verbatim_log) {
              setVerbatimLog(data.verbatim_log);
            }

            // Handle different message types
            switch (data.type) {
              case 'welcome':
                console.log('Welcome message received');
                break;
              case 'processing_progress':
                setProgress(data.percentage || 0);
                break;
              case 'processing_complete':
                setProcessing(false);
                setProgress(100);
                break;
              case 'github_upload_progress':
                console.log('GitHub upload progress:', data.message);
                break;
              case 'github_upload_complete':
                console.log('GitHub upload complete:', data.success);
                break;
              case 'verbatim_log_response':
                setVerbatimLog(data.log || []);
                break;
              default:
                break;
            }
          } catch (e) {
            console.error('WebSocket message error:', e);
          }
        };

      } catch (error) {
        isConnecting = false;
        setConnectionStatus('error');
        console.error('WebSocket connection error:', error);
      }
    };

    // Initial connection
    connectWebSocket();

    // Cleanup function
    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (ws) {
        ws.close();
      }
    };
  }, []); // Empty dependency array - no re-renders!

  // Removed handleWebSocketMessage function to prevent re-render loops
  // Message handling is now inline in the WebSocket onmessage handler

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar(prev => ({ ...prev, open: false }));
  };

  const handleProcessSolar = () => {
    if (!inputFile.trim()) {
      showSnackbar('Please enter an input file', 'error');
      return;
    }
    
    setProcessing(true);
    setProgress(0);
    showSnackbar('Starting solar panel processing...', 'info');
    
    // Simulate processing
    const interval = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval);
          setProcessing(false);
          showSnackbar('Processing completed!', 'success');
          return 100;
        }
        return prev + 10;
      });
    }, 500);
  };

  const handleGitHubUpload = () => {
    if (!websocket) {
      showSnackbar('❌ Not connected to server', 'error');
      return;
    }

    showSnackbar('📤 Starting GitHub upload...', 'info');
    websocket.send(JSON.stringify({
      type: 'github_upload',
      verbose: verboseMode
    }));
  };

  const getStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return '#4caf50';
      case 'disconnected': return '#ff9800';
      case 'error': return '#f44336';
      default: return '#9e9e9e';
    }
  };

  const getStatusText = () => {
    switch (connectionStatus) {
      case 'connected': return 'Connected';
      case 'disconnected': return 'Disconnected';
      case 'error': return 'Error';
      default: return 'Unknown';
    }
  };

  const menuItems = [
    { text: 'Home', icon: <Home />, view: 'home' },
    { text: 'Process Solar Panel', icon: <PhotoCamera />, view: 'process' },
    { text: 'GitHub Upload', icon: <GitHub />, view: 'github' },
    { text: 'Verbatim Log', icon: <Settings />, view: 'verbatim' },
    { text: 'File Browser', icon: <Folder />, view: 'files' },
    { text: 'Settings', icon: <Settings />, view: 'settings' }
  ];

  const renderHomeView = () => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom sx={{ color: '#1976d2', fontWeight: 'bold' }}>
        🌞 Solar Panel Catalog
      </Typography>
      
      <Card sx={{ mb: 2, bgcolor: '#e3f2fd' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Quick Actions
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            <Button
              variant="contained"
              startIcon={<PhotoCamera />}
              onClick={() => setCurrentView('process')}
              sx={{ 
                bgcolor: '#4caf50',
                userSelect: 'text',
                '&:hover': { bgcolor: '#45a049' }
              }}
            >
              Process Solar Panel
            </Button>
            <Button
              variant="contained"
              startIcon={<GitHub />}
              onClick={() => setCurrentView('github')}
              sx={{ 
                bgcolor: '#2196f3',
                userSelect: 'text',
                '&:hover': { bgcolor: '#1976d2' }
              }}
            >
              Upload to GitHub
            </Button>
          </Box>
        </CardContent>
      </Card>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            System Status
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Chip
              label={getStatusText()}
              sx={{ 
                bgcolor: getStatusColor(),
                color: 'white',
                fontWeight: 'bold'
              }}
            />
            <Typography variant="body2" color="text.secondary">
              WebSocket Server
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );

  const renderProcessView = () => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
        🖼️ Process Solar Panel
      </Typography>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <TextField
            fullWidth
            label="Input File Path"
            value={inputFile}
            onChange={(e) => setInputFile(e.target.value)}
            placeholder="solar_panel.jpg"
            sx={{ mb: 2 }}
          />
          
          <TextField
            fullWidth
            label="Output Directory"
            value={outputDir}
            onChange={(e) => setOutputDir(e.target.value)}
            sx={{ mb: 2 }}
          />

          <Box sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={autoUpload}
                  onChange={(e) => setAutoUpload(e.target.checked)}
                />
              }
              label="Auto-upload to GitHub"
            />
          </Box>

          <Box sx={{ mb: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={verboseMode}
                  onChange={(e) => setVerboseMode(e.target.checked)}
                />
              }
              label="Verbose logging"
            />
          </Box>

          {processing && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" gutterBottom>
                Processing... {Math.round(progress)}%
              </Typography>
              <LinearProgress variant="determinate" value={progress} />
            </Box>
          )}

          <Button
            fullWidth
            variant="contained"
            size="large"
            startIcon={<PlayArrow />}
            onClick={handleProcessSolar}
            disabled={processing}
            sx={{ 
              bgcolor: '#4caf50',
              py: 1.5,
              fontSize: '1.1rem',
              userSelect: 'text',
              '&:hover': { bgcolor: '#45a049' }
            }}
          >
            {processing ? 'Processing...' : 'Start Processing'}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );

  const renderGitHubView = () => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
        📤 GitHub Upload
      </Typography>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="body1" gutterBottom>
            Upload your processed solar panel data to GitHub catalog repository with real git commands and verbatim logging.
          </Typography>

          <Alert severity="info" sx={{ mb: 2 }}>
            This will run actual git commands: add, commit, and push to your GitHub repository.
          </Alert>

          <Button
            fullWidth
            variant="contained"
            size="large"
            startIcon={<CloudUpload />}
            onClick={handleGitHubUpload}
            disabled={connectionStatus !== 'connected'}
            sx={{
              bgcolor: '#2196f3',
              py: 1.5,
              fontSize: '1.1rem',
              userSelect: 'text',
              '&:hover': { bgcolor: '#1976d2' },
              '&:disabled': { bgcolor: '#ccc' }
            }}
          >
            {connectionStatus === 'connected' ? 'Upload Latest Results' : 'Server Disconnected'}
          </Button>
        </CardContent>
      </Card>
    </Box>
  );

  const renderVerbatimView = () => (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
        📋 Verbatim Log
      </Typography>

      <Card sx={{ mb: 2 }}>
        <CardContent>
          <Typography variant="body1" gutterBottom>
            Real-time system messages and command output
          </Typography>

          <Box sx={{
            bgcolor: '#000',
            color: '#00ff00',
            p: 2,
            borderRadius: 1,
            fontFamily: 'monospace',
            fontSize: '0.8rem',
            maxHeight: '400px',
            overflowY: 'auto'
          }}>
            {verbatimLog.length > 0 ? (
              verbatimLog.map((line, index) => (
                <div key={index} style={{ marginBottom: '2px' }}>
                  {line}
                </div>
              ))
            ) : (
              <div style={{ color: '#888' }}>No log messages yet...</div>
            )}
          </Box>

          <Button
            variant="outlined"
            onClick={() => {
              if (websocket) {
                websocket.send(JSON.stringify({ type: 'get_verbatim_log' }));
              }
            }}
            sx={{ mt: 2, userSelect: 'text' }}
          >
            Refresh Log
          </Button>
        </CardContent>
      </Card>
    </Box>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case 'home': return renderHomeView();
      case 'process': return renderProcessView();
      case 'github': return renderGitHubView();
      case 'verbatim': return renderVerbatimView();
      case 'files': return (
        <Box sx={{ p: 2 }}>
          <Typography variant="h5">📁 File Browser</Typography>
          <Typography>File browser coming soon...</Typography>
        </Box>
      );
      case 'settings': return (
        <Box sx={{ p: 2 }}>
          <Typography variant="h5">⚙️ Settings</Typography>
          <Typography>Settings panel coming soon...</Typography>
        </Box>
      );
      default: return renderHomeView();
    }
  };

  return (
    <Box sx={{ flexGrow: 1, bgcolor: '#f5f5f5', minHeight: '100vh' }}>
      {/* App Bar */}
      <AppBar position="static" sx={{ bgcolor: '#1976d2' }}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => setDrawerOpen(true)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" sx={{ flexGrow: 1, userSelect: 'text' }}>
            Solar Panel Catalog
          </Typography>
          <Chip
            label={getStatusText()}
            size="small"
            sx={{ 
              bgcolor: getStatusColor(),
              color: 'white'
            }}
          />
        </Toolbar>
      </AppBar>

      {/* Navigation Drawer */}
      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        <Box sx={{ width: 250 }}>
          <List>
            {menuItems.map((item) => (
              <ListItem
                button
                key={item.text}
                onClick={() => {
                  setCurrentView(item.view);
                  setDrawerOpen(false);
                }}
                selected={currentView === item.view}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box sx={{ pb: 8 }}>
        {renderCurrentView()}
      </Box>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
          bgcolor: '#4caf50',
          '&:hover': { bgcolor: '#45a049' }
        }}
        onClick={() => setCurrentView('process')}
      >
        <PhotoCamera />
      </Fab>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={handleCloseSnackbar}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default AndroidApp;
