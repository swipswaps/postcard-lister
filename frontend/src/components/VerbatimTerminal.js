import React, { useEffect, useRef, useState } from 'react';
import {
  Paper,
  Typography,
  Box,
  IconButton,
  Toolbar,
  Chip,
  Switch,
  FormControlLabel,
  Tooltip
} from '@mui/material';
import {
  Clear,
  Download,
  Pause,
  PlayArrow,
  FilterList
} from '@mui/icons-material';

const VerbatimTerminal = ({ output, connectionStatus }) => {
  const terminalRef = useRef(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const [isPaused, setIsPaused] = useState(false);
  const [filter, setFilter] = useState('all'); // all, stdout, stderr, network
  const [displayedOutput, setDisplayedOutput] = useState([]);

  // Auto-scroll to bottom when new output arrives
  useEffect(() => {
    if (autoScroll && terminalRef.current && !isPaused) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [displayedOutput, autoScroll, isPaused]);

  // Filter output based on selected filter
  useEffect(() => {
    if (isPaused) return;

    let filtered = output;
    
    if (filter !== 'all') {
      filtered = output.filter(item => {
        if (filter === 'stdout') return item.type === 'stdout';
        if (filter === 'stderr') return item.type === 'stderr';
        if (filter === 'network') return item.content && item.content.includes('🌐 Network');
        if (filter === 'verbatim') return item.content && item.content.includes('🔧 VERBATIM');
        return true;
      });
    }

    setDisplayedOutput(filtered);
  }, [output, filter, isPaused]);

  const handleClear = () => {
    setDisplayedOutput([]);
  };

  const handleDownload = () => {
    const logContent = displayedOutput
      .map(item => `${new Date(item.timestamp * 1000).toISOString()} [${item.type.toUpperCase()}] ${item.content}`)
      .join('\n');
    
    const blob = new Blob([logContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `solar-panel-terminal-${Date.now()}.log`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const getMessageColor = (type, content) => {
    if (content) {
      if (content.includes('✅')) return '#00ff00'; // Success green
      if (content.includes('❌')) return '#ff4444'; // Error red
      if (content.includes('⚠️')) return '#ffaa00'; // Warning orange
      if (content.includes('🔧 VERBATIM')) return '#00ffff'; // Verbatim cyan
      if (content.includes('🌐 Network')) return '#ff00ff'; // Network magenta
      if (content.includes('📤 STDOUT')) return '#00ff00'; // Stdout green
      if (content.includes('🚨 STDERR')) return '#ff4444'; // Stderr red
    }
    
    switch (type) {
      case 'stdout': return '#00ff00';
      case 'stderr': return '#ff4444';
      case 'system': return '#00ffff';
      default: return '#ffffff';
    }
  };

  const formatTimestamp = (timestamp) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  const getConnectionStatusIcon = () => {
    switch (connectionStatus) {
      case 'connected': return '🟢';
      case 'error': return '🔴';
      default: return '🟡';
    }
  };

  return (
    <Paper 
      elevation={3} 
      sx={{ 
        height: '70vh',
        display: 'flex',
        flexDirection: 'column',
        bgcolor: '#0a0a0a',
        border: '1px solid #333'
      }}
    >
      {/* Terminal Toolbar */}
      <Toolbar 
        variant="dense" 
        sx={{ 
          bgcolor: '#1a1a1a', 
          borderBottom: '1px solid #333',
          minHeight: '48px !important'
        }}
      >
        <Typography variant="h6" sx={{ flexGrow: 1, color: '#00ffff' }}>
          🔧 Verbatim System Output {getConnectionStatusIcon()}
        </Typography>
        
        <Chip
          label={`${displayedOutput.length} messages`}
          size="small"
          sx={{ mr: 1, bgcolor: '#333', color: '#fff' }}
        />

        <FormControlLabel
          control={
            <Switch
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              size="small"
              sx={{ 
                '& .MuiSwitch-switchBase.Mui-checked': { color: '#00ff00' },
                '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { bgcolor: '#00ff00' }
              }}
            />
          }
          label="Auto-scroll"
          sx={{ mr: 1, '& .MuiFormControlLabel-label': { fontSize: '0.8rem', color: '#fff' } }}
        />

        <Tooltip title={isPaused ? "Resume" : "Pause"}>
          <IconButton
            onClick={() => setIsPaused(!isPaused)}
            size="small"
            sx={{ color: isPaused ? '#ffaa00' : '#00ff00', mr: 1 }}
          >
            {isPaused ? <PlayArrow /> : <Pause />}
          </IconButton>
        </Tooltip>

        <Tooltip title="Download Log">
          <IconButton
            onClick={handleDownload}
            size="small"
            sx={{ color: '#00ffff', mr: 1 }}
          >
            <Download />
          </IconButton>
        </Tooltip>

        <Tooltip title="Clear Terminal">
          <IconButton
            onClick={handleClear}
            size="small"
            sx={{ color: '#ff4444' }}
          >
            <Clear />
          </IconButton>
        </Tooltip>
      </Toolbar>

      {/* Filter Bar */}
      <Box sx={{ p: 1, bgcolor: '#1a1a1a', borderBottom: '1px solid #333' }}>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <FilterList sx={{ color: '#fff', mr: 1 }} />
          {['all', 'stdout', 'stderr', 'network', 'verbatim'].map((filterType) => (
            <Chip
              key={filterType}
              label={filterType.toUpperCase()}
              size="small"
              clickable
              onClick={() => setFilter(filterType)}
              sx={{
                bgcolor: filter === filterType ? '#00ff00' : '#333',
                color: filter === filterType ? '#000' : '#fff',
                '&:hover': {
                  bgcolor: filter === filterType ? '#00ff00' : '#555'
                }
              }}
            />
          ))}
        </Box>
      </Box>

      {/* Terminal Output */}
      <Box
        ref={terminalRef}
        sx={{
          flexGrow: 1,
          overflow: 'auto',
          p: 1,
          fontFamily: '"Courier New", monospace',
          fontSize: '12px',
          lineHeight: 1.4,
          bgcolor: '#0a0a0a',
          '&::-webkit-scrollbar': {
            width: '8px',
          },
          '&::-webkit-scrollbar-track': {
            bgcolor: '#1a1a1a',
          },
          '&::-webkit-scrollbar-thumb': {
            bgcolor: '#333',
            borderRadius: '4px',
          },
          '&::-webkit-scrollbar-thumb:hover': {
            bgcolor: '#555',
          },
        }}
      >
        {displayedOutput.length === 0 ? (
          <Box sx={{ textAlign: 'center', mt: 4, color: '#666' }}>
            <Typography variant="body2">
              {isPaused ? '⏸️ Terminal output paused' : '🔧 Waiting for verbatim system output...'}
            </Typography>
            <Typography variant="caption" sx={{ mt: 1, display: 'block' }}>
              Start processing to see real-time terminal output
            </Typography>
          </Box>
        ) : (
          displayedOutput.map((item) => (
            <Box
              key={item.id}
              sx={{
                mb: 0.5,
                p: 0.5,
                borderRadius: '2px',
                '&:hover': {
                  bgcolor: '#1a1a1a'
                }
              }}
            >
              <Typography
                component="div"
                sx={{
                  color: getMessageColor(item.type, item.content),
                  fontFamily: 'inherit',
                  fontSize: 'inherit',
                  whiteSpace: 'pre-wrap',
                  wordBreak: 'break-word'
                }}
              >
                <span style={{ color: '#666', marginRight: '8px' }}>
                  {formatTimestamp(item.timestamp)}
                </span>
                <span style={{ color: '#888', marginRight: '8px' }}>
                  [{item.type.toUpperCase()}]
                </span>
                {item.content}
              </Typography>
            </Box>
          ))
        )}
      </Box>

      {/* Status Bar */}
      <Box 
        sx={{ 
          p: 1, 
          bgcolor: '#1a1a1a', 
          borderTop: '1px solid #333',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}
      >
        <Typography variant="caption" sx={{ color: '#666' }}>
          {isPaused ? '⏸️ Paused' : '▶️ Live'} | Filter: {filter.toUpperCase()} | 
          Connection: {connectionStatus.toUpperCase()}
        </Typography>
        <Typography variant="caption" sx={{ color: '#666' }}>
          🔧 Your signature verbatim capture system in Material UI! 🔍✅
        </Typography>
      </Box>
    </Paper>
  );
};

export default VerbatimTerminal;
