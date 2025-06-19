import React, { useState } from 'react';
import {
  Grid,
  Paper,
  Typography,
  TextField,
  Button,
  Box,
  Card,
  CardContent,
  CardActions,
  Slider,
  FormControlLabel,
  Switch,
  Alert,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  CloudUpload,
  Folder,
  Image,
  PlayArrow,
  Settings
} from '@mui/icons-material';

const ProcessingControl = ({ apiWs, processingStatus, setProcessingStatus }) => {
  const [singleFile, setSingleFile] = useState('');
  const [batchDirectory, setBatchDirectory] = useState('');
  const [outputDirectory, setOutputDirectory] = useState('catalog/');
  const [workers, setWorkers] = useState(4);
  const [verboseMode, setVerboseMode] = useState(true);
  const [autoGithubUpload, setAutoGithubUpload] = useState(false);

  const sendAPIMessage = (message) => {
    if (apiWs && apiWs.readyState === WebSocket.OPEN) {
      apiWs.send(JSON.stringify(message));
      return true;
    } else {
      console.error('API WebSocket not connected');
      return false;
    }
  };

  const handleProcessSingle = () => {
    if (!singleFile.trim()) {
      alert('Please enter a file path');
      return;
    }

    const success = sendAPIMessage({
      type: 'process_single',
      input: singleFile,
      output: outputDirectory,
      verbose: verboseMode,
      github_upload: autoGithubUpload
    });

    if (success) {
      setProcessingStatus('running');
    }
  };

  const handleProcessBatch = () => {
    if (!batchDirectory.trim()) {
      alert('Please enter a directory path');
      return;
    }

    const success = sendAPIMessage({
      type: 'process_batch',
      input: batchDirectory,
      output: outputDirectory,
      workers: workers,
      verbose: verboseMode,
      github_upload: autoGithubUpload
    });

    if (success) {
      setProcessingStatus('running');
    }
  };

  // Removed unused handleStop function

  const getStatusColor = () => {
    switch (processingStatus) {
      case 'running': return 'primary';
      case 'complete': return 'success';
      case 'error': return 'error';
      case 'stopped': return 'warning';
      default: return 'default';
    }
  };

  const getStatusText = () => {
    switch (processingStatus) {
      case 'running': return 'Processing...';
      case 'complete': return 'Complete';
      case 'error': return 'Error';
      case 'stopped': return 'Stopped';
      default: return 'Ready';
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom sx={{ color: '#00ffff', mb: 3 }}>
        🌞 Solar Panel Processing Control
      </Typography>

      {/* Status Bar */}
      <Paper sx={{ p: 2, mb: 3, bgcolor: '#1a1a1a' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Typography variant="h6" sx={{ color: '#fff' }}>
            Processing Status
          </Typography>
          <Chip
            label={getStatusText()}
            color={getStatusColor()}
            sx={{ fontWeight: 'bold' }}
          />
        </Box>
        {processingStatus === 'running' && (
          <LinearProgress 
            sx={{ 
              mt: 2,
              '& .MuiLinearProgress-bar': {
                bgcolor: '#00ff00'
              }
            }} 
          />
        )}
      </Paper>

      <Grid container spacing={3}>
        {/* Single File Processing */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Image sx={{ mr: 1, color: '#ff9800' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  Single Solar Panel
                </Typography>
              </Box>
              
              <TextField
                fullWidth
                label="Solar Panel Image Path"
                value={singleFile}
                onChange={(e) => setSingleFile(e.target.value)}
                placeholder="/path/to/solar_panel.jpg"
                sx={{ 
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    color: '#fff',
                    '& fieldset': { borderColor: '#333' },
                    '&:hover fieldset': { borderColor: '#555' },
                    '&.Mui-focused fieldset': { borderColor: '#00ff00' }
                  },
                  '& .MuiInputLabel-root': { color: '#aaa' }
                }}
              />

              <Alert severity="info" sx={{ mb: 2 }}>
                Process a single solar panel image with AI analysis and GitHub catalog upload.
              </Alert>
            </CardContent>
            
            <CardActions>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={handleProcessSingle}
                disabled={processingStatus === 'running' || !singleFile.trim()}
                sx={{
                  bgcolor: '#00ff00',
                  color: '#000',
                  '&:hover': { bgcolor: '#00cc00' },
                  '&:disabled': { bgcolor: '#333', color: '#666' },
                  userSelect: 'text',
                  WebkitUserSelect: 'text',
                  MozUserSelect: 'text',
                  '& .MuiButton-label': {
                    userSelect: 'text',
                    WebkitUserSelect: 'text',
                    MozUserSelect: 'text'
                  }
                }}
              >
                Process Single Panel
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Batch Processing */}
        <Grid item xs={12} md={6}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Folder sx={{ mr: 1, color: '#ff9800' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  Batch Processing
                </Typography>
              </Box>
              
              <TextField
                fullWidth
                label="Solar Panel Directory"
                value={batchDirectory}
                onChange={(e) => setBatchDirectory(e.target.value)}
                placeholder="/path/to/solar_inventory/"
                sx={{ 
                  mb: 2,
                  '& .MuiOutlinedInput-root': {
                    color: '#fff',
                    '& fieldset': { borderColor: '#333' },
                    '&:hover fieldset': { borderColor: '#555' },
                    '&.Mui-focused fieldset': { borderColor: '#00ff00' }
                  },
                  '& .MuiInputLabel-root': { color: '#aaa' }
                }}
              />

              <Typography gutterBottom sx={{ color: '#fff' }}>
                Parallel Workers: {workers}
              </Typography>
              <Slider
                value={workers}
                onChange={(e, newValue) => setWorkers(newValue)}
                min={1}
                max={16}
                marks
                valueLabelDisplay="auto"
                sx={{
                  color: '#00ff00',
                  '& .MuiSlider-thumb': { bgcolor: '#00ff00' },
                  '& .MuiSlider-track': { bgcolor: '#00ff00' },
                  '& .MuiSlider-rail': { bgcolor: '#333' }
                }}
              />

              <Alert severity="info" sx={{ mt: 2 }}>
                Process multiple solar panels in parallel with {workers} workers.
              </Alert>
            </CardContent>
            
            <CardActions>
              <Button
                variant="contained"
                startIcon={<PlayArrow />}
                onClick={handleProcessBatch}
                disabled={processingStatus === 'running' || !batchDirectory.trim()}
                sx={{
                  bgcolor: '#00ff00',
                  color: '#000',
                  '&:hover': { bgcolor: '#00cc00' },
                  '&:disabled': { bgcolor: '#333', color: '#666' },
                  userSelect: 'text',
                  WebkitUserSelect: 'text',
                  MozUserSelect: 'text',
                  '& .MuiButton-label': {
                    userSelect: 'text',
                    WebkitUserSelect: 'text',
                    MozUserSelect: 'text'
                  }
                }}
              >
                Process Batch
              </Button>
            </CardActions>
          </Card>
        </Grid>

        {/* Settings */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Settings sx={{ mr: 1, color: '#ff9800' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  Processing Settings
                </Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Output Directory"
                    value={outputDirectory}
                    onChange={(e) => setOutputDirectory(e.target.value)}
                    sx={{ 
                      '& .MuiOutlinedInput-root': {
                        color: '#fff',
                        '& fieldset': { borderColor: '#333' },
                        '&:hover fieldset': { borderColor: '#555' },
                        '&.Mui-focused fieldset': { borderColor: '#00ff00' }
                      },
                      '& .MuiInputLabel-root': { color: '#aaa' }
                    }}
                  />
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={verboseMode}
                        onChange={(e) => setVerboseMode(e.target.checked)}
                        sx={{ 
                          '& .MuiSwitch-switchBase.Mui-checked': { color: '#00ff00' },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { bgcolor: '#00ff00' }
                        }}
                      />
                    }
                    label="🔧 Verbatim Capture Mode"
                    sx={{ '& .MuiFormControlLabel-label': { color: '#fff' } }}
                  />
                </Grid>
                
                <Grid item xs={12} md={4}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={autoGithubUpload}
                        onChange={(e) => setAutoGithubUpload(e.target.checked)}
                        sx={{
                          '& .MuiSwitch-switchBase.Mui-checked': { color: '#00ff00' },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { bgcolor: '#00ff00' }
                        }}
                      />
                    }
                    label="🔄 Auto GitHub Upload"
                    sx={{ '& .MuiFormControlLabel-label': { color: '#fff' } }}
                  />
                </Grid>
              </Grid>

              {verboseMode && (
                <Alert severity="success" sx={{ mt: 2 }}>
                  🔧 Verbatim capture enabled - Complete system visibility in terminal output!
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* GitHub Upload Actions */}
        <Grid item xs={12}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CloudUpload sx={{ mr: 1, color: '#ff9800' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  GitHub Catalog Upload
                </Typography>
              </Box>

              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} md={6}>
                  <Alert severity="info">
                    Upload processing results to your GitHub catalog repository with full verbatim capture of the upload process.
                  </Alert>
                </Grid>

                <Grid item xs={12} md={6}>
                  <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      startIcon={<CloudUpload />}
                      onClick={() => {
                        // TODO: Implement manual GitHub upload
                        console.log('Manual GitHub upload triggered');
                      }}
                      disabled={processingStatus === 'running'}
                      sx={{
                        bgcolor: '#00ffff',
                        color: '#000',
                        '&:hover': { bgcolor: '#00cccc' },
                        '&:disabled': { bgcolor: '#333', color: '#666' },
                        userSelect: 'text',
                        WebkitUserSelect: 'text',
                        MozUserSelect: 'text',
                        '& .MuiButton-label': {
                          userSelect: 'text',
                          WebkitUserSelect: 'text',
                          MozUserSelect: 'text'
                        }
                      }}
                    >
                      📤 Upload Latest Results
                    </Button>

                    <Button
                      variant="outlined"
                      startIcon={<CloudUpload />}
                      onClick={() => {
                        // TODO: Implement upload with verbatim capture
                        const success = sendAPIMessage({
                          type: 'github_upload_test',
                          verbose: true
                        });
                        if (success) {
                          console.log('GitHub upload test with verbatim capture started');
                        }
                      }}
                      sx={{
                        borderColor: '#00ff00',
                        color: '#00ff00',
                        '&:hover': { borderColor: '#00cc00', bgcolor: '#001100' },
                        userSelect: 'text',
                        WebkitUserSelect: 'text',
                        MozUserSelect: 'text',
                        '& .MuiButton-label': {
                          userSelect: 'text',
                          WebkitUserSelect: 'text',
                          MozUserSelect: 'text'
                        }
                      }}
                    >
                      🔧 Test Upload with Verbatim
                    </Button>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProcessingControl;
