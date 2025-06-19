import React, { useMemo } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  LinearProgress,
  Chip
} from '@mui/material';
import {
  Analytics,
  Speed,
  CheckCircle,
  NetworkCheck
} from '@mui/icons-material';

const StatusDashboard = ({ terminalOutput, processingStatus }) => {
  const stats = useMemo(() => {
    const totalMessages = terminalOutput.length;
    const successMessages = terminalOutput.filter(msg => 
      msg.content && msg.content.includes('✅')).length;
    const errorMessages = terminalOutput.filter(msg => 
      msg.content && msg.content.includes('❌')).length;
    const networkMessages = terminalOutput.filter(msg => 
      msg.content && msg.content.includes('🌐 Network')).length;
    const verbatimMessages = terminalOutput.filter(msg => 
      msg.content && msg.content.includes('🔧 VERBATIM')).length;

    return {
      totalMessages,
      successMessages,
      errorMessages,
      networkMessages,
      verbatimMessages,
      successRate: totalMessages > 0 ? (successMessages / totalMessages * 100).toFixed(1) : 0
    };
  }, [terminalOutput]);

  const recentActivity = useMemo(() => {
    return terminalOutput
      .slice(-10)
      .reverse()
      .map((msg, index) => ({
        ...msg,
        id: index
      }));
  }, [terminalOutput]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return '#00ff00';
      case 'complete': return '#00ff00';
      case 'error': return '#ff4444';
      default: return '#ffaa00';
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom sx={{ color: '#00ffff', mb: 3 }}>
        📊 System Status Dashboard
      </Typography>

      <Grid container spacing={3}>
        {/* Processing Status */}
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Speed sx={{ mr: 1, color: getStatusColor(processingStatus) }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  Processing
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ color: getStatusColor(processingStatus), mb: 1 }}>
                {processingStatus.toUpperCase()}
              </Typography>
              {processingStatus === 'running' && (
                <LinearProgress 
                  sx={{ 
                    '& .MuiLinearProgress-bar': { bgcolor: '#00ff00' }
                  }} 
                />
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Success Rate */}
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <CheckCircle sx={{ mr: 1, color: '#00ff00' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  Success Rate
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#00ff00', mb: 1 }}>
                {stats.successRate}%
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                {stats.successMessages} / {stats.totalMessages} operations
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Network Activity */}
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <NetworkCheck sx={{ mr: 1, color: '#ff00ff' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  Network
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#ff00ff', mb: 1 }}>
                {stats.networkMessages}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Network operations
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Verbatim Capture */}
        <Grid item xs={12} md={3}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Analytics sx={{ mr: 1, color: '#00ffff' }} />
                <Typography variant="h6" sx={{ color: '#fff' }}>
                  Verbatim
                </Typography>
              </Box>
              <Typography variant="h4" sx={{ color: '#00ffff', mb: 1 }}>
                {stats.verbatimMessages}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                System messages captured
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        {/* Message Statistics */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#fff' }}>
              📈 Message Statistics
            </Typography>
            
            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ color: '#00ff00' }}>
                  Success Messages
                </Typography>
                <Typography variant="body2" sx={{ color: '#00ff00' }}>
                  {stats.successMessages}
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={stats.totalMessages > 0 ? (stats.successMessages / stats.totalMessages * 100) : 0}
                sx={{ 
                  height: 8,
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': { bgcolor: '#00ff00' }
                }}
              />
            </Box>

            <Box sx={{ mb: 2 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ color: '#ff4444' }}>
                  Error Messages
                </Typography>
                <Typography variant="body2" sx={{ color: '#ff4444' }}>
                  {stats.errorMessages}
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={stats.totalMessages > 0 ? (stats.errorMessages / stats.totalMessages * 100) : 0}
                sx={{ 
                  height: 8,
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': { bgcolor: '#ff4444' }
                }}
              />
            </Box>

            <Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2" sx={{ color: '#ff00ff' }}>
                  Network Messages
                </Typography>
                <Typography variant="body2" sx={{ color: '#ff00ff' }}>
                  {stats.networkMessages}
                </Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={stats.totalMessages > 0 ? (stats.networkMessages / stats.totalMessages * 100) : 0}
                sx={{ 
                  height: 8,
                  borderRadius: 4,
                  '& .MuiLinearProgress-bar': { bgcolor: '#ff00ff' }
                }}
              />
            </Box>
          </Paper>
        </Grid>

        {/* Recent Activity */}
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 2, bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#fff' }}>
              🕒 Recent Activity
            </Typography>
            
            <Box sx={{ maxHeight: 300, overflow: 'auto' }}>
              {recentActivity.length === 0 ? (
                <Typography variant="body2" sx={{ color: '#666', textAlign: 'center', mt: 2 }}>
                  No recent activity
                </Typography>
              ) : (
                recentActivity.map((item) => (
                  <Box 
                    key={item.id} 
                    sx={{ 
                      mb: 1, 
                      p: 1, 
                      borderRadius: 1, 
                      bgcolor: '#0a0a0a',
                      border: '1px solid #333'
                    }}
                  >
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 0.5 }}>
                      <Chip
                        label={item.type.toUpperCase()}
                        size="small"
                        sx={{ 
                          mr: 1,
                          bgcolor: item.type === 'stdout' ? '#00ff00' : '#ff4444',
                          color: '#000',
                          fontSize: '0.7rem'
                        }}
                      />
                      <Typography variant="caption" sx={{ color: '#666' }}>
                        {new Date(item.timestamp * 1000).toLocaleTimeString()}
                      </Typography>
                    </Box>
                    <Typography 
                      variant="body2" 
                      sx={{ 
                        color: '#fff',
                        fontFamily: '"Courier New", monospace',
                        fontSize: '0.8rem',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}
                    >
                      {item.content}
                    </Typography>
                  </Box>
                ))
              )}
            </Box>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default StatusDashboard;
