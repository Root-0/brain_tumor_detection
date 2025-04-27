import React, { useState, useEffect, useCallback } from 'react';
import { Upload as UploadIcon, Loader } from 'lucide-react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Container,
  Grid,
  Snackbar,
  Tab,
  Tabs,
  Typography,
  Alert,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Paper,
  Divider,
  Tooltip,
  Chip,
  LinearProgress
} from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import HistoryIcon from '@mui/icons-material/History';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import PendingIcon from '@mui/icons-material/Pending';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';

// Branding: logo SVG (replace with your own if desired)
const BrandLogo = () => (
  <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
    <circle cx="20" cy="20" r="20" fill="#6f42c1" />
    <path d="M15 25 Q20 10 25 25" stroke="#fff" strokeWidth="2.5" fill="none" />
    <circle cx="20" cy="22" r="2.8" fill="#00bcd4" />
  </svg>
);


const BrainTumorDetection = () => {
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [scanId, setScanId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [status, setStatus] = useState('idle'); // idle, uploading, processing, completed, error
  const [statusPolling, setStatusPolling] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [previewUrl, setPreviewUrl] = useState(null);
  const [scanHistory, setScanHistory] = useState([]);
  const [loadingHistory, setLoadingHistory] = useState(false);

  // Mock authentication token - in a real app, get this from your auth system
  const authToken = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkZW1vdXNlciJ9.signature";

  // Backend endpoint URLs
  const API_BASE = process.env.REACT_APP_API_BASE || 'http://localhost:8000/api';

  // Fetch scan history from backend
  const fetchScanHistory = useCallback(async () => {
    if (!authToken) return;
    setLoadingHistory(true);
    try {
      const res = await fetch(`${API_BASE}/users/scans`, {
        headers: { Authorization: `Bearer ${authToken}` }
      });
      if (!res.ok) throw new Error('Failed to fetch scan history');
      const data = await res.json();
      setScanHistory(data);
    } catch (err) {
      setError('Failed to fetch scan history.');
    } finally {
      setLoadingHistory(false);
    }
  }, [authToken]);

  useEffect(() => {
    fetchScanHistory();
  }, [fetchScanHistory]);

  // Handle file selection
  const handleFileChange = (event) => {
    const selected = event.target.files[0];
    setFile(selected);
    setPreviewUrl(selected ? URL.createObjectURL(selected) : null);
    setResult(null);
    setError(null);
  };

  // Upload file to backend
  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setStatus('uploading');
    setError(null);
    setResult(null);
    try {
      const formData = new FormData();
      formData.append('file', file);
      const res = await fetch(`${API_BASE}/predict`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
        body: formData
      });
      if (!res.ok) throw new Error('Upload failed');
      const data = await res.json();
      setScanId(data.scan_id);
      setStatus('processing');
      pollResult(data.scan_id);
    } catch (err) {
      setError('Upload failed.');
      setStatus('error');
    } finally {
      setUploading(false);
    }
  };

  // Poll scan result
  const pollResult = async (scanId) => {
    setStatusPolling(setInterval(async () => {
      try {
        const res = await fetch(`${API_BASE}/predict/${scanId}`, {
          headers: { Authorization: `Bearer ${authToken}` }
        });
        if (!res.ok) throw new Error('Failed to get result');
        const data = await res.json();
        if (data.status === 'completed') {
          setResult(data.result);
          setStatus('completed');
          clearInterval(statusPolling);
          fetchScanHistory();
        } else if (data.status === 'failed') {
          setError('Scan failed.');
          setStatus('error');
          clearInterval(statusPolling);
        }
      } catch (err) {
        setError('Error polling scan result.');
        setStatus('error');
        clearInterval(statusPolling);
      }
    }, 3000));
  };

  // Tab change
  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
    setError(null);
    setResult(null);
    setFile(null);
    setPreviewUrl(null);
  };

  // UI rendering
  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Card variant="outlined" sx={{ mb: 4 }}>
        <CardHeader
          avatar={<Avatar sx={{ bgcolor: 'background.paper', width: 56, height: 56 }}><BrandLogo /></Avatar>}
          title={<Typography variant="h4" sx={{ fontWeight: 800, color: 'primary.main', letterSpacing: '-2px' }}>NeuroDetect</Typography>}
          subheader={<Typography variant="subtitle1" sx={{ color: 'secondary.main', fontWeight: 600 }}>AI Brain Tumor Detection</Typography>}
        />
        <CardContent> 
          <Tabs value={activeTab} onChange={handleTabChange} centered>
            <Tab icon={<UploadIcon />} label="Upload Scan" value="upload" />
            <Tab icon={<HistoryIcon />} label="History" value="history" />
          </Tabs>
          <Divider sx={{ my: 2 }} />
          {activeTab === 'upload' && (
            <Box>
              <Grid container spacing={2} alignItems="center">
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="contained"
                    component="label"
                    startIcon={<CloudUploadIcon />}
                    fullWidth
                    disabled={uploading}
                  >
                    Select MRI Scan
                    <input type="file" hidden accept=".dcm,.nii,.nii.gz,.img,.hdr" onChange={handleFileChange} />
                  </Button>
                  {file && (
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Selected: {file.name}
                    </Typography>
                  )}
                  {previewUrl && (
                    <Box sx={{ mt: 2 }}>
                      <Typography variant="caption">Preview:</Typography>
                      <Paper variant="outlined" sx={{ p: 1, mt: 1 }}>
                        <InsertDriveFileIcon fontSize="large" color="action" />
                        <Typography variant="body2">{file.name}</Typography>
                      </Paper>
                    </Box>
                  )}
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Button
                    variant="contained"
                    color="primary"
                    onClick={handleUpload}
                    disabled={!file || uploading}
                    fullWidth
                    sx={{ height: 56 }}
                  >
                    {uploading ? <CircularProgress size={24} /> : 'Upload & Detect'}
                  </Button>
                </Grid>
              </Grid>
              {status === 'processing' && (
                <Box sx={{ mt: 3, textAlign: 'center' }}>
                  <CircularProgress />
                  <Typography variant="body2" sx={{ mt: 2 }}>Processing scan, please wait...</Typography>
                </Box>
              )}
              {result && (
                <Box sx={{ mt: 3 }}>
                  <Card variant="outlined" sx={{ bgcolor: 'background.paper', p: 2, borderColor: result.prediction?.tumor_detected ? 'warning.main' : 'success.main' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                      <Avatar sx={{ bgcolor: result.prediction?.tumor_detected ? 'warning.main' : 'success.main', width: 56, height: 56 }}>
                        {result.prediction?.tumor_detected ? <ErrorIcon fontSize="large" /> : <CheckCircleIcon fontSize="large" />}
                      </Avatar>
                      <Box>
                        <Typography variant="h6" sx={{ fontWeight: 700 }}>
                          {result.prediction?.tumor_detected ? 'Tumor Detected' : 'No Tumor Detected'}
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Confidence:
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                          <LinearProgress
                            variant="determinate"
                            value={result.prediction?.confidence * 100}
                            sx={{ width: 120, height: 10, borderRadius: 5, bgcolor: 'grey.800', '& .MuiLinearProgress-bar': { bgcolor: result.prediction?.tumor_detected ? 'warning.main' : 'success.main' } }}
                          />
                          <Typography variant="body2" sx={{ minWidth: 48, fontWeight: 700 }}>{(result.prediction?.confidence * 100).toFixed(1)}%</Typography>
                        </Box>
                        {result.prediction?.tumor_detected && (
                          <Chip label={`Tumor Size: ${result.prediction.tumor_size_ml} ml`} color="warning" variant="outlined" sx={{ mt: 1, fontWeight: 700 }} />
                        )}
                      </Box>
                    </Box>
                  </Card>
                </Box>
              )}
              {error && (
                <Box sx={{ mt: 3 }}>
                  <Alert severity="error">{error}</Alert>
                </Box>
              )}
            </Box>
          )}
          {activeTab === 'history' && (
            <Box>
              {loadingHistory ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                  <CircularProgress />
                </Box>
              ) : (
                <List>
                  {scanHistory.length === 0 && (
                    <Typography variant="body2">No scans found.</Typography>
                  )}
                  {scanHistory.map((scan) => (
                    <React.Fragment key={scan.scan_id}>
                      <ListItem alignItems="flex-start">
                        <ListItemAvatar>
                          <Avatar sx={{ bgcolor: scan.status === 'completed' ? 'success.main' : scan.status === 'failed' ? 'error.main' : 'warning.main' }}>
                            {scan.status === 'completed' ? <CheckCircleIcon /> : scan.status === 'failed' ? <ErrorIcon /> : <PendingIcon />}
                          </Avatar>
                        </ListItemAvatar>
                        <ListItemText
                          primary={scan.filename}
                          secondary={
                            <>
                              <Typography component="span" variant="body2" color="text.primary">
                                Status: {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
                              </Typography>
                              <br />
                              Uploaded: {new Date(scan.created_at).toLocaleString()}
                              {scan.result && scan.result.prediction && (
                                <>
                                  <br />
                                  <b>{scan.result.prediction.tumor_detected ? 'Tumor Detected' : 'No Tumor'}</b>
                                  <br />
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
                                    <LinearProgress
                                      variant="determinate"
                                      value={scan.result.prediction.confidence * 100}
                                      sx={{ width: 80, height: 7, borderRadius: 4, bgcolor: 'grey.800', '& .MuiLinearProgress-bar': { bgcolor: scan.result.prediction.tumor_detected ? 'warning.main' : 'success.main' } }}
                                    />
                                    <Typography variant="caption" sx={{ minWidth: 32, fontWeight: 700 }}>{(scan.result.prediction.confidence * 100).toFixed(1)}%</Typography>
                                  </Box>
                                  {scan.result.prediction.tumor_detected && (
                                    <Chip label={`Tumor Size: ${scan.result.prediction.tumor_size_ml} ml`} color="warning" size="small" variant="outlined" sx={{ mt: 0.5, fontWeight: 700 }} />
                                  )}
                                </>
                              )}
                            </>
                          }
                        />
                      </ListItem>
                      <Divider component="li" />
                    </React.Fragment>
                  ))}
                </List>
              )}
            </Box>
          )}
        </CardContent>
      </Card>
      <Snackbar open={!!error} autoHideDuration={6000} onClose={() => setError(null)}>
        <Alert onClose={() => setError(null)} severity="error" sx={{ width: '100%' }}>
          {error}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default BrainTumorDetection;
