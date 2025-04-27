import React, { useState, useEffect, useCallback } from 'react';
// Fix: Import icons from lucide-react and UI components from a proper UI library
import { Upload as UploadIcon, Loader } from 'lucide-react';

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
  
  // Fetch scan history
  const fetchScanHistory = useCallback(async () => {
    if (!authToken) return;
    
    setLoadingHistory(true);
    try {
      // In a real app, this would be a fetch to your API
      setLoadingHistory(false);
      // Mocked data for demo
      setScanHistory([
        { 
          scan_id: 'scan-123',
          filename: 'patient1_t1.dcm',
          status: 'completed',
          created_at: '2025-04-24T09:30:45Z',
          result: {
            prediction: {
              tumor_detected: true,
              confidence: 0.92,
              tumor_size_ml: 3.4
            }
          }
        },
        { 
          scan_id: 'scan-456',
          filename: 'patient2_flair.nii',
          status: 'completed',
          created_at: '2025-04-23T14:15:22Z', 
          result: {
            prediction: {
              tumor_detected: false,
              confidence: 0.87,
              tumor_size_ml: 0
            }
          }
        }
      ]);
    } catch (err) {
      setError('Failed to load scan history');
      setLoadingHistory(false);
    }
  }, [authToken]);

  // Load scan history when component mounts
  useEffect(() => {
    fetchScanHistory();
  }, [fetchScanHistory]);

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError(null);
      
      // Create preview for the file (if possible)
      if (selectedFile.type.includes('image/')) {
        const reader = new FileReader();
        reader.onloadend = () => {
          setPreviewUrl(reader.result);
        };
        reader.readAsDataURL(selectedFile);
      } else {
        // For non-image files like DICOM/NIfTI, show a placeholder
        setPreviewUrl('/api/placeholder/400/320');
      }
    }
  };

  // Upload and process the file
  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file first');
      return;
    }

    setUploading(true);
    setStatus('uploading');
    setError(null);

    try {
      // Create form data for the API request
      const formData = new FormData();
      formData.append('file', file);

      // In a real app, this would be a fetch to your API
      // const response = await fetch('http://your-api-url/api/predict', {
      //   method: 'POST',
      //   headers: {
      //     'Authorization': `Bearer ${authToken}`
      //   },
      //   body: formData
      // });
      
      // Mock API response
      await new Promise(resolve => setTimeout(resolve, 1500));
      const mockResponse = {
        scan_id: 'mock-scan-' + Math.random().toString(36).substring(2, 8),
        status: 'processing'
      };
      
      setScanId(mockResponse.scan_id);
      setStatus('processing');
      setUploading(false);
      
      // Start polling for results
      startResultPolling(mockResponse.scan_id);
    } catch (err) {
      setError('Upload failed. Please try again.');
      setStatus('error');
      setUploading(false);
    }
  };

  // Poll for results
  const startResultPolling = (id) => {
    // Clear any existing polling
    if (statusPolling) clearInterval(statusPolling);
    
    // Set up polling every 2 seconds
    const intervalId = setInterval(async () => {
      try {
        // In a real app, this would fetch from your API
        // const response = await fetch(`http://your-api-url/api/predict/${id}`, {
        //   headers: {
        //     'Authorization': `Bearer ${authToken}`
        //   }
        // });
        
        // Mock the polling response
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // After 3 seconds, simulate completion
        if (Date.now() % 5 > 3) {
          clearInterval(intervalId);
          setStatusPolling(null);
          setStatus('completed');
          
          // Mock result
          const mockResult = {
            prediction: {
              tumor_detected: Math.random() > 0.5,
              confidence: 0.88 + Math.random() * 0.1,
              tumor_size_ml: Math.random() > 0.5 ? 2.8 + Math.random() * 3 : 0,
              tumor_center: [128, 112, 75]
            },
            metadata: {
              processing_time: 4.32,
              model_version: "unet_resnet50_v1.0"
            }
          };
          
          setResult(mockResult);
          setActiveTab('results');
          
          // Update history
          setScanHistory(prev => [{
            scan_id: id,
            filename: file.name,
            status: 'completed',
            created_at: new Date().toISOString(),
            result: mockResult
          }, ...prev]);
        }
      } catch (err) {
        clearInterval(intervalId);
        setStatusPolling(null);
        setError('Failed to get scan results');
        setStatus('error');
      }
    }, 2000);
    
    setStatusPolling(intervalId);
  };

  // Clean up on unmount
  useEffect(() => {
    return () => {
      if (statusPolling) clearInterval(statusPolling);
    };
  }, [statusPolling]);

  // Fix: Added rendering for results tab
  const renderResults = () => {
    if (!result) {
      return <div className="text-center py-8">No results to display. Process a scan first.</div>;
    }

    const { prediction, metadata } = result;
    
    return (
      <div className="space-y-6">
        <div className="bg-white border rounded-lg p-6">
          <h3 className="text-xl font-bold mb-4">Analysis Results</h3>
          
          <div className="mb-6">
            <div className={`text-lg font-bold mb-2 ${prediction.tumor_detected ? 'text-red-600' : 'text-green-600'}`}>
              {prediction.tumor_detected ? 'Tumor Detected' : 'No Tumor Detected'}
            </div>
            <div className="text-sm text-gray-500">Confidence: {(prediction.confidence * 100).toFixed(1)}%</div>
          </div>
          
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Tumor Size:</span>
              <span>{prediction.tumor_size_ml > 0 ? `${prediction.tumor_size_ml.toFixed(1)} ml` : 'N/A'}</span>
            </div>
            
            {prediction.tumor_center && (
              <div className="flex justify-between">
                <span>Tumor Center (xyz):</span>
                <span>{prediction.tumor_center.join(', ')}</span>
              </div>
            )}
            
            <div className="flex justify-between">
              <span>Processing Time:</span>
              <span>{metadata.processing_time.toFixed(2)} seconds</span>
            </div>
            
            <div className="flex justify-between">
              <span>Model Version:</span>
              <span>{metadata.model_version}</span>
            </div>
          </div>
        </div>
        
        {previewUrl && (
          <div className="bg-white border rounded-lg p-6">
            <h3 className="text-lg font-bold mb-4">Scan Image</h3>
            <div className="flex justify-center">
              <img src={previewUrl} alt="Brain scan" className="max-h-64 object-contain" />
            </div>
          </div>
        )}
      </div>
    );
  };

  // Fix: Added rendering for history tab
  const renderHistory = () => {
    if (loadingHistory) {
      return (
        <div className="flex justify-center py-8">
          <Loader className="animate-spin" />
          <span className="ml-2">Loading history...</span>
        </div>
      );
    }

    if (scanHistory.length === 0) {
      return <div className="text-center py-8">No scan history available.</div>;
    }

    return (
      <div className="space-y-4">
        {scanHistory.map(scan => (
          <div key={scan.scan_id} className="bg-white border rounded-lg p-4">
            <div className="flex justify-between items-center mb-2">
              <h4 className="font-medium">{scan.filename}</h4>
              <div className={`px-2 py-1 rounded text-sm ${
                scan.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-blue-100 text-blue-800'
              }`}>
                {scan.status.charAt(0).toUpperCase() + scan.status.slice(1)}
              </div>
            </div>
            
            <div className="text-sm text-gray-500 mb-2">
              {new Date(scan.created_at).toLocaleString()}
            </div>
            
            {scan.result && scan.result.prediction && (
              <div className="mt-2 pt-2 border-t">
                <div className={`font-medium ${
                  scan.result.prediction.tumor_detected ? 'text-red-600' : 'text-green-600'
                }`}>
                  {scan.result.prediction.tumor_detected ? 'Tumor Detected' : 'No Tumor Detected'}
                </div>
                <div className="text-sm text-gray-600">
                  Confidence: {(scan.result.prediction.confidence * 100).toFixed(1)}%
                </div>
                {scan.result.prediction.tumor_size_ml > 0 && (
                  <div className="text-sm text-gray-600">
                    Size: {scan.result.prediction.tumor_size_ml.toFixed(1)} ml
                  </div>
                )}
              </div>
            )}
            
            <button 
              className="mt-2 text-blue-600 text-sm hover:underline"
              onClick={() => {
                setResult(scan.result);
                setActiveTab('results');
              }}
            >
              View Details
            </button>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex flex-col w-full max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Brain Tumor Detection System</h1>
      
      <div className="w-full">
        <div className="flex border-b mb-4">
          <div 
            className={`px-4 py-2 cursor-pointer ${activeTab === 'upload' ? 'border-b-2 border-blue-500 font-semibold' : ''}`}
            onClick={() => setActiveTab('upload')}
          >
            Upload Scan
          </div>
          <div 
            className={`px-4 py-2 cursor-pointer ${activeTab === 'results' ? 'border-b-2 border-blue-500 font-semibold' : ''}`}
            onClick={() => setActiveTab('results')}
          >
            Results
          </div>
          <div 
            className={`px-4 py-2 cursor-pointer ${activeTab === 'history' ? 'border-b-2 border-blue-500 font-semibold' : ''}`}
            onClick={() => setActiveTab('history')}
          >
            Scan History
          </div>
        </div>
        
        {activeTab === 'upload' && (
          <div className="space-y-6">
            <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <div className="flex justify-center mb-4">
                <UploadIcon size={48} className="text-gray-400" />
              </div>
              <h3 className="text-lg font-medium mb-2">Upload MRI Scan</h3>
              <p className="text-gray-500 mb-4">Supported formats: DICOM (.dcm), NIfTI (.nii, .nii.gz)</p>
              
              <input
                type="file"
                id="file-upload"
                onChange={handleFileChange}
                className="hidden"
                accept=".dcm,.nii,.nii.gz"
              />
              
              <div className="flex justify-center">
                <label htmlFor="file-upload" className="bg-blue-600 text-white py-2 px-4 rounded cursor-pointer hover:bg-blue-700">
                  Select File
                </label>
              </div>
            </div>
            
            {file && (
              <div className="bg-white border rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">{file.name}</h4>
                    <p className="text-gray-500 text-sm">
                      {(file.size / (1024 * 1024)).toFixed(2)} MB
                    </p>
                  </div>
                  
                  {!uploading && status !== 'processing' && (
                    <button
                      onClick={handleUpload}
                      className="bg-green-600 text-white py-2 px-4 rounded hover:bg-green-700"
                    >
                      Process Scan
                    </button>
                  )}
                  
                  {(uploading || status === 'processing') && (
                    <div className="flex items-center">
                      <Loader className="animate-spin mr-2" />
                      <span>{uploading ? 'Uploading...' : 'Processing...'}</span>
                    </div>
                  )}
                </div>
                
                {previewUrl && (
                  <div className="mt-4 flex justify-center">
                    <img src={previewUrl} alt="Scan preview" className="max-h-64 object-contain" />
                  </div>
                )}
                
                {status === 'processing' && (
                  <div className="mt-4">
                    <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
                      <div className="bg-blue-500 h-full" style={{ width: '45%' }}></div>
                    </div>
                    <p className="text-center text-sm text-gray-500 mt-1">Processing scan... This may take a few minutes.</p>
                  </div>
                )}
              </div>
            )}
            
            {error && (
              <div className="bg-red-50 border border-red-200 p-4 rounded-lg">
                <div className="text-red-800">{error}</div>
              </div>
            )}
          </div>
        )}
        
        {activeTab === 'results' && renderResults()}
        
        {activeTab === 'history' && renderHistory()}
      </div>
    </div>
  );
};

export default BrainTumorDetection;