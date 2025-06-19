import React, { useMemo } from 'react';
import {
  Grid,
  Paper,
  Typography,
  Box,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button
} from '@mui/material';
import {
  Download,
  GitHub,
  CheckCircle,
  Error
} from '@mui/icons-material';

const ResultsViewer = ({ terminalOutput }) => {
  const processedItems = useMemo(() => {
    const items = [];
    let currentItem = null;

    terminalOutput.forEach((msg) => {
      if (msg.content) {
        // Start of new processing
        if (msg.content.includes('🌞 SOLAR PANEL PROCESSING') || 
            msg.content.includes('🔄 Starting processing')) {
          if (currentItem) {
            items.push(currentItem);
          }
          currentItem = {
            id: Date.now() + Math.random(),
            startTime: msg.timestamp,
            status: 'processing',
            file: 'Unknown',
            productId: null,
            images: 0,
            analysis: null,
            errors: []
          };
        }

        // Extract file information
        if (currentItem && msg.content.includes('📁 Input:')) {
          const match = msg.content.match(/📁 Input: (.+)/);
          if (match) {
            currentItem.file = match[1];
          }
        }

        // Extract processing results
        if (currentItem && msg.content.includes('✅ Image processed:')) {
          const match = msg.content.match(/(\d+) variants/);
          if (match) {
            currentItem.images = parseInt(match[1]);
          }
        }

        // Extract product ID
        if (currentItem && msg.content.includes('✅ GitHub catalog upload completed:')) {
          const match = msg.content.match(/completed: (.+)/);
          if (match) {
            currentItem.productId = match[1];
          }
        }

        // Extract AI analysis confidence
        if (currentItem && msg.content.includes('confidence')) {
          const match = msg.content.match(/confidence (\d+\.?\d*)/);
          if (match) {
            currentItem.analysis = parseFloat(match[1]);
          }
        }

        // Track errors
        if (currentItem && msg.content.includes('❌')) {
          currentItem.errors.push(msg.content);
          currentItem.status = 'error';
        }

        // Mark as complete
        if (currentItem && msg.content.includes('✅ CSV generated:')) {
          currentItem.status = 'complete';
          currentItem.endTime = msg.timestamp;
        }
      }
    });

    // Add the last item if it exists
    if (currentItem) {
      items.push(currentItem);
    }

    return items.reverse(); // Show most recent first
  }, [terminalOutput]);

  const summary = useMemo(() => {
    const total = processedItems.length;
    const completed = processedItems.filter(item => item.status === 'complete').length;
    const errors = processedItems.filter(item => item.status === 'error').length;
    const processing = processedItems.filter(item => item.status === 'processing').length;

    return { total, completed, errors, processing };
  }, [processedItems]);

  const getStatusColor = (status) => {
    switch (status) {
      case 'complete': return 'success';
      case 'error': return 'error';
      case 'processing': return 'primary';
      default: return 'default';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'complete': return <CheckCircle />;
      case 'error': return <Error />;
      default: return null;
    }
  };

  const formatDuration = (startTime, endTime) => {
    if (!endTime) return 'In progress...';
    const duration = endTime - startTime;
    return `${duration.toFixed(1)}s`;
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h5" gutterBottom sx={{ color: '#00ffff', mb: 3 }}>
        📋 Processing Results
      </Typography>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={3}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ color: '#fff' }}>
                {summary.total}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Total Processed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={3}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ color: '#00ff00' }}>
                {summary.completed}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Completed
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={3}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ color: '#ff4444' }}>
                {summary.errors}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Errors
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={3}>
          <Card sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
            <CardContent sx={{ textAlign: 'center' }}>
              <Typography variant="h4" sx={{ color: '#ffaa00' }}>
                {summary.processing}
              </Typography>
              <Typography variant="body2" sx={{ color: '#aaa' }}>
                Processing
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Results Table */}
      <Paper sx={{ bgcolor: '#1a1a1a', border: '1px solid #333' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ '& th': { bgcolor: '#2a2a2a', color: '#fff', borderBottom: '1px solid #333' } }}>
                <TableCell>Status</TableCell>
                <TableCell>File</TableCell>
                <TableCell>Product ID</TableCell>
                <TableCell>Images</TableCell>
                <TableCell>AI Confidence</TableCell>
                <TableCell>Duration</TableCell>
                <TableCell>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {processedItems.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={7} sx={{ textAlign: 'center', color: '#666', py: 4 }}>
                    No processing results yet. Start processing to see results here.
                  </TableCell>
                </TableRow>
              ) : (
                processedItems.map((item) => (
                  <TableRow 
                    key={item.id}
                    sx={{ 
                      '& td': { 
                        color: '#fff', 
                        borderBottom: '1px solid #333' 
                      },
                      '&:hover': {
                        bgcolor: '#2a2a2a'
                      }
                    }}
                  >
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(item.status)}
                        label={item.status.toUpperCase()}
                        color={getStatusColor(item.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography 
                        variant="body2" 
                        sx={{ 
                          fontFamily: '"Courier New", monospace',
                          maxWidth: 200,
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}
                      >
                        {item.file}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {item.productId ? (
                        <Typography variant="body2" sx={{ fontFamily: '"Courier New", monospace' }}>
                          {item.productId}
                        </Typography>
                      ) : (
                        <Typography variant="body2" sx={{ color: '#666' }}>
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {item.images > 0 ? item.images : '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      {item.analysis ? (
                        <Chip
                          label={`${(item.analysis * 100).toFixed(1)}%`}
                          size="small"
                          sx={{
                            bgcolor: item.analysis > 0.8 ? '#00ff00' : item.analysis > 0.6 ? '#ffaa00' : '#ff4444',
                            color: '#000'
                          }}
                        />
                      ) : (
                        <Typography variant="body2" sx={{ color: '#666' }}>
                          -
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ fontFamily: '"Courier New", monospace' }}>
                        {formatDuration(item.startTime, item.endTime)}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {item.productId && (
                          <Button
                            size="small"
                            startIcon={<GitHub />}
                            sx={{ color: '#00ffff', minWidth: 'auto' }}
                          >
                            View
                          </Button>
                        )}
                        {item.status === 'complete' && (
                          <Button
                            size="small"
                            startIcon={<Download />}
                            sx={{ color: '#00ff00', minWidth: 'auto' }}
                          >
                            CSV
                          </Button>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Error Details */}
      {processedItems.some(item => item.errors.length > 0) && (
        <Paper sx={{ mt: 3, p: 2, bgcolor: '#1a1a1a', border: '1px solid #ff4444' }}>
          <Typography variant="h6" gutterBottom sx={{ color: '#ff4444' }}>
            ❌ Error Details
          </Typography>
          {processedItems
            .filter(item => item.errors.length > 0)
            .map((item) => (
              <Box key={item.id} sx={{ mb: 2 }}>
                <Typography variant="subtitle2" sx={{ color: '#fff', mb: 1 }}>
                  {item.file}:
                </Typography>
                {item.errors.map((error, index) => (
                  <Typography 
                    key={index}
                    variant="body2" 
                    sx={{ 
                      color: '#ff4444',
                      fontFamily: '"Courier New", monospace',
                      ml: 2,
                      mb: 0.5
                    }}
                  >
                    {error}
                  </Typography>
                ))}
              </Box>
            ))}
        </Paper>
      )}
    </Box>
  );
};

export default ResultsViewer;
