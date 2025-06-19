import React, { useState, useRef, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  AppBar,
  Toolbar,
  Chip,
  Alert,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider
} from '@mui/material';
import {
  PhotoCamera,
  CloudUpload,
  GitHub,
  Menu as MenuIcon,
  Home,
  Settings,
  Terminal,
  Folder
} from '@mui/icons-material';

const StableApp = () => {
  // Stable state - no unnecessary re-renders
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [inputFile, setInputFile] = useState('');
  const [message, setMessage] = useState('');
  const [messageType, setMessageType] = useState('info');
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [currentView, setCurrentView] = useState('home');
  const [verbatimLog, setVerbatimLog] = useState([]);
  const [gitStatus, setGitStatus] = useState(null);
  const [uploadEvidence, setUploadEvidence] = useState(null);
  const [processingResults, setProcessingResults] = useState(null);
  const [batchResults, setBatchResults] = useState(null);
  const [fileList, setFileList] = useState([]);
  const [currentDirectory, setCurrentDirectory] = useState('.');
  const [commitMessage, setCommitMessage] = useState('Solar panel catalog update');

  // Use ref to prevent re-renders
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  // Stable WebSocket connection - no re-render loops
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8081');
        wsRef.current = ws;
        
        ws.onopen = () => {
          setConnectionStatus('connected');
          setMessage('✅ Connected to server');
          setMessageType('success');
          console.log('WebSocket connected');
        };
        
        ws.onclose = () => {
          setConnectionStatus('disconnected');
          setMessage('🔌 Disconnected from server');
          setMessageType('warning');
          wsRef.current = null;
          
          // Reconnect after 5 seconds
          if (!reconnectTimeoutRef.current) {
            reconnectTimeoutRef.current = setTimeout(() => {
              reconnectTimeoutRef.current = null;
              connectWebSocket();
            }, 5000);
          }
        };
        
        ws.onerror = () => {
          setConnectionStatus('error');
          setMessage('❌ Connection error');
          setMessageType('error');
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('WebSocket message:', data);

            // Update verbatim log if present
            if (data.verbatim_log) {
              setVerbatimLog(data.verbatim_log);
            }

            // Update git status if present
            if (data.git_status) {
              setGitStatus(data.git_status);
            }

            // Update upload evidence if present
            if (data.evidence) {
              setUploadEvidence(data.evidence);
            }

            switch (data.type) {
              case 'welcome':
                setMessage('🌞 Connected to Solar Panel Catalog');
                setMessageType('success');
                if (data.git_status) {
                  setGitStatus(data.git_status);
                }
                break;
              case 'processing_progress':
                setMessage(data.description || 'Processing...');
                setMessageType('info');
                break;
              case 'processing_complete':
                setMessage('✅ Processing completed!');
                setMessageType('success');
                break;
              case 'github_upload_progress':
                // Extract the actual verbatim message from the system output
                let verbatimMessage = data.message || 'Uploading...';

                // Clean up the message to show actual system output
                if (verbatimMessage.includes('📤 STDOUT:')) {
                  verbatimMessage = verbatimMessage.replace(/.*📤 STDOUT:\s*/, '');
                }
                if (verbatimMessage.includes('🚨 STDERR:')) {
                  verbatimMessage = verbatimMessage.replace(/.*🚨 STDERR:\s*/, '');
                }

                // Remove color codes for cleaner display
                verbatimMessage = verbatimMessage.replace(/\[0;\d+m|\[0m/g, '');

                setMessage(verbatimMessage);
                setMessageType('info');
                break;
              case 'github_upload_complete':
                if (data.success) {
                  if (data.evidence && data.evidence.staged_files && data.evidence.staged_files.length > 0) {
                    setMessage(`✅ Successfully uploaded ${data.evidence.staged_files.length} files to GitHub!`);
                  } else if (data.evidence && data.evidence.verbatim_stdout && data.evidence.verbatim_stdout.length > 0) {
                    // Show the last actual system message
                    const lastMessage = data.evidence.verbatim_stdout[data.evidence.verbatim_stdout.length - 1];
                    setMessage(lastMessage.replace(/\[0;\d+m|\[0m/g, ''));
                  } else {
                    setMessage(data.message || '✅ Successfully uploaded to GitHub!');
                  }
                  setMessageType('success');
                } else {
                  setMessage(`❌ Upload failed: ${data.message}`);
                  setMessageType('error');
                }
                if (data.evidence) {
                  setUploadEvidence(data.evidence);
                }
                break;
              case 'verbatim_log_response':
                setVerbatimLog(data.log || []);
                break;
              case 'solar_panel_processing_complete':
                if (data.success) {
                  setMessage('✅ Solar panel processing completed!');
                  setMessageType('success');
                  setProcessingResults(data.results);
                } else {
                  setMessage(`❌ Processing failed: ${data.message}`);
                  setMessageType('error');
                }
                break;
              case 'batch_processing_progress':
                setMessage(`🔄 Batch processing: ${data.processed}/${data.total} completed`);
                setMessageType('info');
                break;
              case 'batch_processing_complete':
                if (data.success) {
                  setMessage(`✅ Batch processing completed! ${data.results.processed}/${data.results.total_files} successful`);
                  setMessageType('success');
                  setBatchResults(data.results);
                } else {
                  setMessage(`❌ Batch processing failed: ${data.message}`);
                  setMessageType('error');
                }
                break;
              case 'ebay_csv_generation_complete':
                if (data.success) {
                  setMessage(`✅ eBay CSV generated with ${data.results.product_count} products!`);
                  setMessageType('success');
                } else {
                  setMessage(`❌ CSV generation failed: ${data.message}`);
                  setMessageType('error');
                }
                break;
              case 'file_list_response':
                if (data.success) {
                  setFileList(data.files || []);
                  setCurrentDirectory(data.directory);
                } else {
                  setMessage(`❌ File listing failed: ${data.message}`);
                  setMessageType('error');
                }
                break;
              default:
                break;
            }
          } catch (e) {
            console.error('WebSocket message error:', e);
          }
        };
        
      } catch (error) {
        setConnectionStatus('error');
        setMessage('❌ Failed to connect');
        setMessageType('error');
      }
    };

    connectWebSocket();
    
    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []); // Empty deps - no re-renders!

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

  const handleProcessSolar = () => {
    if (!inputFile.trim()) {
      setMessage('❌ Please enter an input file');
      setMessageType('error');
      return;
    }
    
    setMessage('🔧 Processing solar panel...');
    setMessageType('info');
    
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ 
        type: 'process_solar_panel',
        file: inputFile
      }));
    } else {
      setMessage('❌ Not connected to server');
      setMessageType('error');
    }
  };

  const handleGitHubUpload = () => {
    setMessage('📤 Starting GitHub upload...');
    setMessageType('info');

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'github_upload',
        commit_message: commitMessage,
        verbose: true
      }));
    } else {
      setMessage('❌ Not connected to server');
      setMessageType('error');
    }
  };

  const handleBatchProcess = () => {
    if (!inputFile.trim()) {
      setMessage('❌ Please enter an input directory');
      setMessageType('error');
      return;
    }

    setMessage('🔄 Starting batch processing...');
    setMessageType('info');

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'batch_process',
        input_dir: inputFile,
        workers: 4
      }));
    } else {
      setMessage('❌ Not connected to server');
      setMessageType('error');
    }
  };

  const handleGenerateEbayCSV = () => {
    setMessage('📄 Generating eBay CSV...');
    setMessageType('info');

    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'generate_ebay_csv'
      }));
    } else {
      setMessage('❌ Not connected to server');
      setMessageType('error');
    }
  };

  const handleListFiles = (directory = '.') => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'list_files',
        directory: directory
      }));
    } else {
      setMessage('❌ Not connected to server');
      setMessageType('error');
    }
  };

  const menuItems = [
    { text: 'Home', icon: <Home />, view: 'home' },
    { text: 'Process Solar Panel', icon: <PhotoCamera />, view: 'process' },
    { text: 'Batch Processing', icon: <CloudUpload />, view: 'batch' },
    { text: 'eBay CSV Generator', icon: <Settings />, view: 'ebay' },
    { text: 'GitHub Upload', icon: <GitHub />, view: 'github' },
    { text: 'File Browser', icon: <Folder />, view: 'files' },
    { text: 'Verbatim Log', icon: <Terminal />, view: 'verbatim' },
    { text: 'Settings', icon: <Settings />, view: 'settings' }
  ];

  const cleanVerbatimMessage = (message) => {
    // MINIMAL cleaning - preserve ALL system content for troubleshooting
    let cleaned = message;

    // Only remove the LLM wrapper timestamp, keep everything else
    cleaned = cleaned.replace(/^\d{2}:\d{2}:\d{2}\.\d{3} \[INFO\] /, '');

    // Extract actual system output from STDOUT/STDERR markers but keep the content
    if (cleaned.includes('📤 STDOUT:')) {
      cleaned = cleaned.replace(/.*📤 STDOUT:\s*/, '');
    }
    if (cleaned.includes('🚨 STDERR:')) {
      cleaned = cleaned.replace(/.*🚨 STDERR:\s*/, '');
    }

    // Keep color codes for now - they help identify message types
    // cleaned = cleaned.replace(/\[0;\d+m|\[0m/g, '');

    // Keep timestamps - they're critical for troubleshooting
    // cleaned = cleaned.replace(/^Jun \d+ \d{2}:\d{2}:\d{2} /, '');

    // Return ALL content - no filtering
    return cleaned.trim();
  };

  const renderUploadEvidence = () => {
    if (!uploadEvidence) return null;

    return (
      <Card sx={{ mb: 3, bgcolor: '#f8f9fa' }}>
        <CardContent>
          <Typography variant="h6" gutterBottom sx={{ color: '#1976d2' }}>
            📊 Upload Evidence
          </Typography>

          {uploadEvidence.staged_files && uploadEvidence.staged_files.length > 0 && (
            <>
              <Typography variant="subtitle1" gutterBottom>
                📁 Files Uploaded ({uploadEvidence.staged_files.length}):
              </Typography>
              <Box sx={{
                bgcolor: '#fff',
                p: 2,
                borderRadius: 1,
                border: '1px solid #ddd',
                maxHeight: '200px',
                overflowY: 'auto',
                mb: 2
              }}>
                {uploadEvidence.staged_files.map((file, index) => (
                  <Typography key={index} variant="body2" sx={{ fontFamily: 'monospace' }}>
                    📄 {file}
                  </Typography>
                ))}
              </Box>
            </>
          )}

          {/* Show ALL verbatim system output - complete troubleshooting data */}
          {uploadEvidence.verbatim_stdout && uploadEvidence.verbatim_stdout.length > 0 && (
            <>
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                📤 Complete System Output (STDOUT) - {uploadEvidence.verbatim_stdout.length} lines:
              </Typography>
              <Box sx={{
                bgcolor: '#000',
                color: '#00ff00',
                p: 2,
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                maxHeight: '400px',
                overflowY: 'auto',
                mb: 2
              }}>
                {uploadEvidence.verbatim_stdout.map((line, index) => {
                  let cleanLine = cleanVerbatimMessage(line);

                  // Color code for better readability but show ALL lines
                  let color = '#00ff00';
                  if (cleanLine.includes('[ERROR]') || cleanLine.includes('failed') || cleanLine.includes('error:')) {
                    color = '#ff6666';
                  } else if (cleanLine.includes('[SUCCESS]')) {
                    color = '#00ff00';
                  } else if (cleanLine.includes('[INFO]') || cleanLine.includes('create mode') || cleanLine.includes('files changed')) {
                    color = '#66ccff';
                  } else if (cleanLine.includes('remote:') || cleanLine.includes('warning:')) {
                    color = '#ffaa00';
                  }

                  return (
                    <div key={index} style={{ marginBottom: '1px', color }}>
                      {cleanLine}
                    </div>
                  );
                })}
              </Box>
            </>
          )}

          {/* Show ALL verbatim error output */}
          {uploadEvidence.verbatim_stderr && uploadEvidence.verbatim_stderr.length > 0 && (
            <>
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                🚨 Complete System Errors (STDERR) - {uploadEvidence.verbatim_stderr.length} lines:
              </Typography>
              <Box sx={{
                bgcolor: '#000',
                color: '#ff6666',
                p: 2,
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                maxHeight: '300px',
                overflowY: 'auto',
                mb: 2
              }}>
                {uploadEvidence.verbatim_stderr.map((line, index) => (
                  <div key={index} style={{ marginBottom: '1px' }}>
                    {cleanVerbatimMessage(line)}
                  </div>
                ))}
              </Box>
            </>
          )}

          {/* Show combined verbatim output if available */}
          {uploadEvidence.verbatim_combined && uploadEvidence.verbatim_combined.length > 0 && (
            <>
              <Typography variant="subtitle1" gutterBottom sx={{ mt: 2 }}>
                📋 Complete Combined Output - {uploadEvidence.verbatim_combined.length} lines:
              </Typography>
              <Box sx={{
                bgcolor: '#000',
                color: '#00ff00',
                p: 2,
                borderRadius: 1,
                fontFamily: 'monospace',
                fontSize: '0.75rem',
                maxHeight: '500px',
                overflowY: 'auto',
                mb: 2
              }}>
                {uploadEvidence.verbatim_combined.map((line, index) => {
                  let cleanLine = cleanVerbatimMessage(line);

                  // Color code for better readability
                  let color = '#00ff00';
                  if (cleanLine.includes('[ERROR]') || cleanLine.includes('failed') || cleanLine.includes('error:')) {
                    color = '#ff6666';
                  } else if (cleanLine.includes('[SUCCESS]')) {
                    color = '#00ff00';
                  } else if (cleanLine.includes('[INFO]') || cleanLine.includes('create mode') || cleanLine.includes('files changed')) {
                    color = '#66ccff';
                  } else if (cleanLine.includes('remote:') || cleanLine.includes('warning:')) {
                    color = '#ffaa00';
                  }

                  return (
                    <div key={index} style={{ marginBottom: '1px', color }}>
                      {cleanLine}
                    </div>
                  );
                })}
              </Box>
            </>
          )}

          {uploadEvidence.commit_message && (
            <Typography variant="body2" gutterBottom>
              💾 <strong>Commit:</strong> {uploadEvidence.commit_message}
            </Typography>
          )}

          {uploadEvidence.exit_code !== undefined && (
            <Typography variant="body2" gutterBottom>
              🔧 <strong>Exit Code:</strong> {uploadEvidence.exit_code}
            </Typography>
          )}

          {uploadEvidence.repo_url && (
            <Typography variant="body2" gutterBottom>
              🌐 <strong>Repository:</strong> {uploadEvidence.repo_url}
            </Typography>
          )}

          {uploadEvidence.recent_commits && uploadEvidence.recent_commits.length > 0 && (
            <>
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                📋 Recent Commits:
              </Typography>
              <Box sx={{
                bgcolor: '#fff',
                p: 2,
                borderRadius: 1,
                border: '1px solid #ddd',
                fontFamily: 'monospace',
                fontSize: '0.8rem'
              }}>
                {uploadEvidence.recent_commits.slice(0, 5).map((commit, index) => (
                  <div key={index}>{commit}</div>
                ))}
              </Box>
            </>
          )}

          {/* Show log file locations */}
          {uploadEvidence.log_files && (
            <>
              <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
                📁 Verbatim Log Files:
              </Typography>
              <Box sx={{
                bgcolor: '#fff',
                p: 2,
                borderRadius: 1,
                border: '1px solid #ddd',
                fontFamily: 'monospace',
                fontSize: '0.8rem'
              }}>
                {uploadEvidence.log_files.stdout && (
                  <div>📤 STDOUT: {uploadEvidence.log_files.stdout}</div>
                )}
                {uploadEvidence.log_files.stderr && (
                  <div>🚨 STDERR: {uploadEvidence.log_files.stderr}</div>
                )}
                {uploadEvidence.log_files.combined && (
                  <div>📋 Combined: {uploadEvidence.log_files.combined}</div>
                )}
              </Box>
            </>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderBatchView = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
          🔄 Batch Processing
        </Typography>

        <Typography variant="body1" gutterBottom>
          Process multiple solar panels in parallel with multi-LLM analysis
        </Typography>

        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Input Directory"
            value={inputFile}
            onChange={(e) => setInputFile(e.target.value)}
            placeholder="e.g., solar_inventory/"
            sx={{ mb: 2 }}
          />

          <Button
            variant="contained"
            onClick={handleBatchProcess}
            disabled={connectionStatus !== 'connected'}
            sx={{ mr: 2 }}
          >
            🔄 Start Batch Processing
          </Button>

          <Button
            variant="outlined"
            onClick={() => handleListFiles('.')}
            disabled={connectionStatus !== 'connected'}
          >
            📁 Browse Files
          </Button>
        </Box>

        {batchResults && (
          <Card sx={{ bgcolor: '#f8f9fa', mb: 2 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                📊 Batch Results
              </Typography>
              <Typography variant="body2">
                📁 Total Files: {batchResults.total_files}
              </Typography>
              <Typography variant="body2">
                ✅ Processed: {batchResults.processed}
              </Typography>
              <Typography variant="body2">
                ❌ Failed: {batchResults.failed}
              </Typography>
              <Typography variant="body2">
                📈 Success Rate: {batchResults.success_rate?.toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        )}
      </CardContent>
    </Card>
  );

  const renderEbayView = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
          📄 eBay CSV Generator
        </Typography>

        <Typography variant="body1" gutterBottom>
          Generate professional eBay listings from processed solar panel data
        </Typography>

        <Box sx={{ mb: 3 }}>
          <Button
            variant="contained"
            onClick={handleGenerateEbayCSV}
            disabled={connectionStatus !== 'connected'}
            sx={{ mr: 2 }}
          >
            📄 Generate eBay CSV
          </Button>

          <Button
            variant="outlined"
            onClick={() => handleListFiles('catalog/')}
            disabled={connectionStatus !== 'connected'}
          >
            📁 View Catalog
          </Button>
        </Box>

        <Alert severity="info" sx={{ mb: 2 }}>
          This will create a CSV file with all processed solar panels ready for eBay upload.
          Make sure you have processed some solar panels first.
        </Alert>
      </CardContent>
    </Card>
  );

  const renderFilesView = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
          📁 File Browser
        </Typography>

        <Typography variant="body1" gutterBottom>
          Browse and select files for processing
        </Typography>

        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" sx={{ mb: 1 }}>
            Current Directory: {currentDirectory}
          </Typography>

          <Button
            variant="outlined"
            onClick={() => handleListFiles(currentDirectory)}
            disabled={connectionStatus !== 'connected'}
            sx={{ mr: 2 }}
          >
            🔄 Refresh
          </Button>

          <Button
            variant="outlined"
            onClick={() => handleListFiles('..')}
            disabled={connectionStatus !== 'connected'}
          >
            ⬆️ Parent Directory
          </Button>
        </Box>

        <Box sx={{
          maxHeight: '400px',
          overflowY: 'auto',
          border: '1px solid #ddd',
          borderRadius: 1,
          p: 1
        }}>
          {fileList.length > 0 ? (
            fileList.map((file, index) => (
              <Box
                key={index}
                sx={{
                  p: 1,
                  mb: 1,
                  bgcolor: file.type === 'directory' ? '#e3f2fd' : '#f5f5f5',
                  borderRadius: 1,
                  cursor: 'pointer',
                  '&:hover': { bgcolor: file.type === 'directory' ? '#bbdefb' : '#eeeeee' }
                }}
                onClick={() => {
                  if (file.type === 'directory') {
                    handleListFiles(file.path);
                  } else {
                    setInputFile(file.path);
                  }
                }}
              >
                <Typography variant="body2">
                  {file.type === 'directory' ? '📁' : file.is_image ? '🖼️' : '📄'} {file.name}
                  {file.size && ` (${(file.size / 1024).toFixed(1)} KB)`}
                </Typography>
              </Box>
            ))
          ) : (
            <Typography variant="body2" color="text.secondary">
              No files found. Click Refresh to load files.
            </Typography>
          )}
        </Box>
      </CardContent>
    </Card>
  );

  const renderVerbatimView = () => (
    <Card sx={{ mb: 3 }}>
      <CardContent>
        <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
          📋 Verbatim System Log
        </Typography>

        <Typography variant="body1" gutterBottom>
          Real-time system messages and command output (actual verbatim capture, not LLM-generated)
        </Typography>

        <Alert severity="info" sx={{ mb: 2 }}>
          This shows actual system output from GitHub CLI and git commands, captured using tee patterns.
          Color codes and timestamps are preserved from the original system output.
        </Alert>

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
            verbatimLog.map((line, index) => {
              // MINIMAL cleaning - show ALL messages for troubleshooting
              let cleanLine = cleanVerbatimMessage(line);

              // ONLY skip completely empty lines - show everything else
              if (!cleanLine.trim()) {
                return null;
              }

              // Color code based on content but show ALL messages
              let color = '#00ff00'; // Default green
              if (cleanLine.includes('[SUCCESS]') || cleanLine.includes('authenticated')) {
                color = '#00ff00'; // Green for success
              } else if (cleanLine.includes('[ERROR]') || cleanLine.includes('failed') || cleanLine.includes('error:') || cleanLine.includes('remote rejected')) {
                color = '#ff6666'; // Red for errors
              } else if (cleanLine.includes('[INFO]') || cleanLine.includes('main ') || cleanLine.includes('files changed') || cleanLine.includes('create mode')) {
                color = '#66ccff'; // Blue for info
              } else if (cleanLine.includes('remote:') || cleanLine.includes('warning:')) {
                color = '#ffaa00'; // Orange for remote messages
              } else if (cleanLine.includes('PUSH PROTECTION') || cleanLine.includes('secrets') || cleanLine.includes('GITHUB')) {
                color = '#ff9900'; // Orange for security warnings
              } else if (cleanLine.includes('📨') || cleanLine.includes('Client') || cleanLine.includes('Starting') || cleanLine.includes('Running')) {
                color = '#888888'; // Gray for LLM metadata but still show it
              }

              return (
                <div key={index} style={{ marginBottom: '1px', color, fontSize: '0.8rem', fontFamily: 'monospace' }}>
                  {cleanLine}
                </div>
              );
            })
          ) : (
            <div style={{ color: '#888' }}>No system messages yet...</div>
          )}
        </Box>

        <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            onClick={() => {
              if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                wsRef.current.send(JSON.stringify({ type: 'get_verbatim_log' }));
              }
            }}
          >
            Refresh System Log
          </Button>

          <Button
            variant="outlined"
            onClick={() => setVerbatimLog([])}
          >
            Clear Display
          </Button>
        </Box>
      </CardContent>
    </Card>
  );

  const renderCurrentView = () => {
    switch (currentView) {
      case 'home':
        return (
          <>
            {/* Process Solar Panel */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
                  🖼️ Process Solar Panel
                </Typography>

                <TextField
                  fullWidth
                  label="Input File Path"
                  value={inputFile}
                  onChange={(e) => setInputFile(e.target.value)}
                  placeholder="solar_panel.jpg"
                  sx={{ mb: 2 }}
                />

                <Button
                  fullWidth
                  variant="contained"
                  size="large"
                  startIcon={<PhotoCamera />}
                  onClick={handleProcessSolar}
                  disabled={connectionStatus !== 'connected'}
                  sx={{
                    bgcolor: '#4caf50',
                    py: 1.5,
                    fontSize: '1.1rem',
                    '&:hover': { bgcolor: '#45a049' },
                    '&:disabled': { bgcolor: '#ccc' }
                  }}
                >
                  {connectionStatus === 'connected' ? 'Process Solar Panel' : 'Server Disconnected'}
                </Button>
              </CardContent>
            </Card>

            {/* GitHub Upload - Enhanced Main Page */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
                  📤 GitHub Upload
                </Typography>

                <Typography variant="body1" gutterBottom>
                  Upload your processed solar panel data to GitHub repository with real git commands.
                </Typography>

                <Alert severity="info" sx={{ mb: 2 }}>
                  This will run actual git commands: add, commit, and push to your GitHub repository.
                </Alert>

                <TextField
                  fullWidth
                  label="Commit Message"
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                  placeholder="Solar panel catalog update"
                  sx={{ mb: 2 }}
                />

                {gitStatus && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    🌐 Repository: {gitStatus.repo_url}<br/>
                    🌿 Branch: {gitStatus.branch}<br/>
                    📝 Current commit: {gitStatus.current_commit}
                  </Alert>
                )}

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
                    '&:hover': { bgcolor: '#1976d2' },
                    '&:disabled': { bgcolor: '#ccc' }
                  }}
                >
                  {connectionStatus === 'connected' ? 'Upload to GitHub' : 'Server Disconnected'}
                </Button>

                {/* Real-Time Progress on Main Page - Enhanced UX */}
                {verbatimLog.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Typography variant="h6" sx={{ color: '#1976d2', mr: 2 }}>
                          📋 Live System Output
                        </Typography>
                        <Chip
                          label={`${verbatimLog.length} messages`}
                          size="small"
                          sx={{ bgcolor: '#e3f2fd' }}
                        />
                      </Box>

                      {/* Save/Copy Buttons */}
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => {
                            const logText = verbatimLog.join('\n');
                            navigator.clipboard.writeText(logText).then(() => {
                              setMessage('📋 Log copied to clipboard!');
                              setMessageType('success');
                            }).catch(() => {
                              setMessage('❌ Failed to copy to clipboard');
                              setMessageType('error');
                            });
                          }}
                          sx={{ fontSize: '0.75rem' }}
                        >
                          📋 Copy Log
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => {
                            const logText = verbatimLog.join('\n');
                            const blob = new Blob([logText], { type: 'text/plain' });
                            const url = URL.createObjectURL(blob);
                            const a = document.createElement('a');
                            a.href = url;
                            a.download = `github_upload_log_${new Date().toISOString().slice(0,19).replace(/:/g,'-')}.txt`;
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                            URL.revokeObjectURL(url);
                            setMessage('💾 Log saved to file!');
                            setMessageType('success');
                          }}
                          sx={{ fontSize: '0.75rem' }}
                        >
                          💾 Save Log
                        </Button>
                        <Button
                          size="small"
                          variant="outlined"
                          onClick={() => setCurrentView('verbatim')}
                          sx={{ fontSize: '0.75rem' }}
                        >
                          🔍 Full Log
                        </Button>
                      </Box>
                    </Box>

                    <Typography variant="body2" gutterBottom sx={{ color: '#666' }}>
                      Real verbatim capture from git and GitHub CLI (not LLM-generated)
                    </Typography>

                    {/* Enhanced GitHub Actions Style Terminal */}
                    <Box
                      ref={(el) => {
                        if (el) {
                          // Auto-scroll to bottom when new messages arrive
                          el.scrollTop = el.scrollHeight;
                        }
                      }}
                      sx={{
                        bgcolor: '#0d1117',
                        color: '#c9d1d9',
                        p: 2,
                        borderRadius: 2,
                        fontFamily: 'SFMono-Regular, Consolas, "Liberation Mono", Menlo, monospace',
                        fontSize: '0.875rem',
                        maxHeight: '400px',  // Increased height
                        overflowY: 'auto',
                        border: '1px solid #30363d',
                        position: 'relative'
                      }}
                    >
                      {verbatimLog.slice(-50).map((logEntry, index) => {  // Show more messages
                        // Parse message type and content
                        const isError = logEntry.includes('[ERROR]') || logEntry.includes('error:') || logEntry.includes('failed') || logEntry.includes('rejected');
                        const isSuccess = logEntry.includes('[SUCCESS]') || logEntry.includes('Successfully') || logEntry.includes('authenticated');
                        const isNetwork = logEntry.includes('[NETWORK]') || logEntry.includes('remote:') || logEntry.includes('github.com');
                        const isProgress = logEntry.includes('[PROGRESS]') || logEntry.includes('Counting') || logEntry.includes('Compressing') || logEntry.includes('Writing');
                        const isGit = logEntry.includes('[GIT]') || logEntry.includes('main ') || logEntry.includes('files changed');

                        // Extract timestamp if present
                        const timeMatch = logEntry.match(/(\d{2}:\d{2}:\d{2})/);
                        const timestamp = timeMatch ? timeMatch[1] : '';

                        return (
                          <Box
                            key={index}
                            sx={{
                              py: 0.25,
                              display: 'flex',
                              alignItems: 'flex-start',
                              borderLeft: isError ? '2px solid #f85149' :
                                         isSuccess ? '2px solid #3fb950' :
                                         isNetwork ? '2px solid #58a6ff' :
                                         isProgress ? '2px solid #f0883e' :
                                         isGit ? '2px solid #a5a5a5' : 'none',
                              pl: isError || isSuccess || isNetwork || isProgress || isGit ? 1 : 0,
                              '&:hover': { bgcolor: 'rgba(255,255,255,0.05)' }
                            }}
                          >
                            {timestamp && (
                              <Box sx={{
                                color: '#7d8590',
                                fontSize: '0.75rem',
                                mr: 1,
                                minWidth: '60px',
                                fontFamily: 'monospace'
                              }}>
                                {timestamp}
                              </Box>
                            )}
                            <Box sx={{
                              color: isError ? '#f85149' :
                                     isSuccess ? '#3fb950' :
                                     isNetwork ? '#58a6ff' :
                                     isProgress ? '#f0883e' :
                                     isGit ? '#ffa657' : '#c9d1d9',
                              flex: 1,
                              wordBreak: 'break-word'
                            }}>
                              {logEntry.replace(/^\d{2}:\d{2}:\d{2}[.\d]*\s*\[?\w*\]?\s*/, '')}
                            </Box>
                          </Box>
                        );
                      })}

                      {/* Enhanced Status indicator */}
                      <Box sx={{
                        position: 'absolute',
                        top: 8,
                        right: 8,
                        bgcolor: 'rgba(0,0,0,0.8)',
                        px: 1.5,
                        py: 0.5,
                        borderRadius: 1,
                        fontSize: '0.75rem',
                        color: '#7d8590',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 1
                      }}>
                        <Box sx={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          bgcolor: '#3fb950',
                          animation: 'pulse 2s infinite'
                        }} />
                        {verbatimLog.length > 50 ? `Last 50 of ${verbatimLog.length}` : `${verbatimLog.length} total`}
                      </Box>
                    </Box>

                    {/* Enhanced Quick Actions */}
                    <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => setCurrentView('verbatim')}
                        sx={{ fontSize: '0.75rem' }}
                      >
                        🔍 Full Log View
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                            wsRef.current.send(JSON.stringify({ type: 'get_verbatim_log' }));
                          }
                        }}
                        sx={{ fontSize: '0.75rem' }}
                      >
                        🔄 Refresh
                      </Button>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          // Clear the log display
                          setVerbatimLog([]);
                          setMessage('🧹 Log display cleared');
                          setMessageType('info');
                        }}
                        sx={{ fontSize: '0.75rem' }}
                      >
                        🧹 Clear Display
                      </Button>
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>

            {/* Upload Evidence */}
            {renderUploadEvidence()}
          </>
        );
      case 'process':
        return (
          <>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
                  🖼️ Advanced Solar Panel Processing
                </Typography>

                <Typography variant="body1" gutterBottom>
                  Multi-LLM analysis with image processing and GitHub catalog integration
                </Typography>

                <TextField
                  fullWidth
                  label="Input File Path"
                  value={inputFile}
                  onChange={(e) => setInputFile(e.target.value)}
                  placeholder="solar_panel.jpg"
                  sx={{ mb: 2 }}
                />

                <Box sx={{ mb: 2 }}>
                  <Button
                    variant="contained"
                    size="large"
                    startIcon={<PhotoCamera />}
                    onClick={handleProcessSolar}
                    disabled={connectionStatus !== 'connected'}
                    sx={{
                      bgcolor: '#4caf50',
                      py: 1.5,
                      fontSize: '1.1rem',
                      mr: 2,
                      '&:hover': { bgcolor: '#45a049' },
                      '&:disabled': { bgcolor: '#ccc' }
                    }}
                  >
                    {connectionStatus === 'connected' ? 'Process Solar Panel' : 'Server Disconnected'}
                  </Button>

                  <Button
                    variant="outlined"
                    onClick={() => handleListFiles('.')}
                    disabled={connectionStatus !== 'connected'}
                  >
                    📁 Browse Files
                  </Button>
                </Box>

                <Alert severity="info" sx={{ mb: 2 }}>
                  This will analyze the solar panel using multiple AI models, process images into multiple variants,
                  extract technical specifications, and upload to GitHub catalog for eBay integration.
                </Alert>
              </CardContent>
            </Card>

            {processingResults && (
              <Card sx={{ bgcolor: '#f8f9fa', mb: 3 }}>
                <CardContent>
                  <Typography variant="h6" gutterBottom sx={{ color: '#1976d2' }}>
                    📊 Processing Results
                  </Typography>
                  <Typography variant="body2">
                    🏷️ Product Type: {processingResults.product_type}
                  </Typography>
                  <Typography variant="body2">
                    🎯 Confidence: {(processingResults.confidence * 100).toFixed(1)}%
                  </Typography>
                  <Typography variant="body2">
                    🖼️ Images Processed: {Object.keys(processingResults.processed_images || {}).length}
                  </Typography>
                  <Typography variant="body2">
                    📤 Catalog ID: {processingResults.catalog_result?.product_id || 'N/A'}
                  </Typography>
                </CardContent>
              </Card>
            )}
          </>
        );
      case 'batch':
        return renderBatchView();
      case 'ebay':
        return renderEbayView();
      case 'files':
        return renderFilesView();
      case 'github':
        return (
          <>
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
                  📤 GitHub Upload
                </Typography>

                <Typography variant="body1" gutterBottom>
                  Upload your processed solar panel data to GitHub repository with real git commands.
                </Typography>

                <Alert severity="info" sx={{ mb: 2 }}>
                  This will run actual git commands: add, commit, and push to your GitHub repository.
                </Alert>

                <TextField
                  fullWidth
                  label="Commit Message"
                  value={commitMessage}
                  onChange={(e) => setCommitMessage(e.target.value)}
                  placeholder="Solar panel catalog update"
                  sx={{ mb: 2 }}
                />

                {gitStatus && (
                  <Alert severity="info" sx={{ mb: 2 }}>
                    🌐 Repository: {gitStatus.repo_url}<br/>
                    🌿 Branch: {gitStatus.branch}<br/>
                    📝 Current commit: {gitStatus.current_commit}<br/>
                    📊 Has changes: {gitStatus.has_changes ? 'Yes' : 'No'}
                  </Alert>
                )}

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
                    '&:hover': { bgcolor: '#1976d2' },
                    '&:disabled': { bgcolor: '#ccc' }
                  }}
                >
                  {connectionStatus === 'connected' ? 'Upload to GitHub' : 'Server Disconnected'}
                </Button>
              </CardContent>
            </Card>

            {/* Upload Evidence */}
            {renderUploadEvidence()}

            {/* Verbatim Log in GitHub view */}
            <Card sx={{ mb: 3 }}>
              <CardContent>
                <Typography variant="h6" gutterBottom sx={{ color: '#1976d2' }}>
                  📋 Actual System Command Output
                </Typography>

                <Typography variant="body2" gutterBottom sx={{ color: '#666' }}>
                  Real verbatim capture from GitHub CLI and git commands (not LLM-generated)
                </Typography>

                <Box sx={{
                  bgcolor: '#000',
                  color: '#00ff00',
                  p: 2,
                  borderRadius: 1,
                  fontFamily: 'monospace',
                  fontSize: '0.8rem',
                  maxHeight: '300px',
                  overflowY: 'auto'
                }}>
                  {verbatimLog.length > 0 ? (
                    verbatimLog.slice(-50).map((line, index) => {
                      // MINIMAL cleaning - show ALL system output for troubleshooting
                      let cleanLine = cleanVerbatimMessage(line);

                      // ONLY skip completely empty lines - show EVERYTHING else
                      if (!cleanLine.trim()) {
                        return null;
                      }

                      // Color code but show ALL messages including metadata
                      let color = '#00ff00'; // Default green
                      if (cleanLine.includes('[SUCCESS]') || cleanLine.includes('authenticated')) {
                        color = '#00ff00'; // Green for success
                      } else if (cleanLine.includes('[ERROR]') || cleanLine.includes('failed') || cleanLine.includes('error:') || cleanLine.includes('rejected')) {
                        color = '#ff6666'; // Red for errors
                      } else if (cleanLine.includes('[INFO]') || cleanLine.includes('main ') || cleanLine.includes('files changed') || cleanLine.includes('create mode') || cleanLine.includes('insertions') || cleanLine.includes('deletions')) {
                        color = '#66ccff'; // Blue for info
                      } else if (cleanLine.includes('remote:') || cleanLine.includes('warning:') || cleanLine.includes('To https://')) {
                        color = '#ffaa00'; // Orange for remote messages
                      } else if (cleanLine.includes('PROTECTION') || cleanLine.includes('secrets') || cleanLine.includes('GITHUB') || cleanLine.includes('blob id')) {
                        color = '#ff9900'; // Orange for security
                      } else if (cleanLine.includes('📨') || cleanLine.includes('Client') || cleanLine.includes('Starting') || cleanLine.includes('Running') || cleanLine.includes('Captured')) {
                        color = '#888888'; // Gray for metadata but still show it
                      }

                      return (
                        <div key={index} style={{ marginBottom: '1px', color, fontSize: '0.8rem', fontFamily: 'monospace' }}>
                          {cleanLine}
                        </div>
                      );
                    })
                  ) : (
                    <div style={{ color: '#888' }}>No command output yet...</div>
                  )}
                </Box>

                <Button
                  variant="outlined"
                  size="small"
                  onClick={() => {
                    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
                      wsRef.current.send(JSON.stringify({ type: 'get_verbatim_log' }));
                    }
                  }}
                  sx={{ mt: 2 }}
                >
                  Refresh System Output
                </Button>
              </CardContent>
            </Card>
          </>
        );
      case 'verbatim':
        return renderVerbatimView();

      case 'settings':
        return (
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h5" gutterBottom sx={{ color: '#1976d2' }}>
                ⚙️ Settings
              </Typography>
              <Typography>Settings panel coming soon...</Typography>
            </CardContent>
          </Card>
        );
      default:
        return null;
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
          <Typography variant="h6" sx={{ flexGrow: 1 }}>
            🌞 Solar Panel Catalog
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
          <Divider />
          <List>
            <ListItem>
              <ListItemText
                primary="Connection Status"
                secondary={getStatusText()}
              />
            </ListItem>
          </List>
        </Box>
      </Drawer>

      {/* Main Content */}
      <Box sx={{ p: 3, maxWidth: 800, mx: 'auto' }}>

        {/* Status Message */}
        {message && (
          <Alert
            severity={messageType}
            sx={{ mb: 3 }}
            onClose={() => setMessage('')}
          >
            {message}
          </Alert>
        )}

        {/* Render Current View */}
        {renderCurrentView()}

        {/* System Info - Always visible */}
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              📊 System Information
            </Typography>
            <Typography variant="body2" color="text.secondary">
              WebSocket Server: ws://localhost:8081<br/>
              Status: {getStatusText()}<br/>
              Features: Real git commands, verbatim logging, Android UI<br/>
              Current View: {currentView}
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Box>
  );
};

export default StableApp;
