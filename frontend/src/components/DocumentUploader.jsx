import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { uploadDocuments, getIngestionStatus } from '../services/api';

function DocumentUploader() {
  const [uploading, setUploading] = useState(false);
  const [jobId, setJobId] = useState(null);
  const [status, setStatus] = useState(null);

  const onDrop = useCallback(async (acceptedFiles) => {
    setUploading(true);
    setStatus(null);
    try {
      const result = await uploadDocuments(acceptedFiles);
      setJobId(result.job_id);

      // Poll for status
      const interval = setInterval(async () => {
        try {
          const statusResult = await getIngestionStatus(result.job_id);
          setStatus(statusResult);
          if (statusResult.status === 'completed' || statusResult.status === 'failed') {
            clearInterval(interval);
            setUploading(false);
          }
        } catch (pollError) {
            console.error('Polling error:', pollError);
            clearInterval(interval);
            setUploading(false);
        }
      }, 2000);

    } catch (err) {
      console.error('Upload error:', err);
      setUploading(false);
      setStatus({ status: 'failed', error: err.response?.data?.detail || 'Upload failed' });
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'text/plain': ['.txt'],
    }
  });

  return (
    <div>
      <h2>Document Upload</h2>
      <div {...getRootProps()} style={{ border: '2px dashed #ccc', padding: '20px', textAlign: 'center' }}>
        <input {...getInputProps()} />
        {isDragActive ? (
          <p>Drop files here...</p>
        ) : (
          <div>
            <p>Drag & drop files here, or click to select</p>
            <p>Supported: PDF, DOCX, TXT (Max 10MB)</p>
          </div>
        )}
      </div>
      {uploading && !status && <p>Uploading...</p>}
      {status && (
        <div>
          <div>
            <span>Status: {status.status}</span>
            <span> {status.processed}/{status.total}</span>
          </div>
          {status.status === 'processing' && (
            <div style={{ width: '100%', backgroundColor: '#eee' }}>
              <div style={{width: `${status.progress * 100}%`, backgroundColor: 'blue', height: '20px' }}></div>
            </div>
          )}
          {status.status === 'failed' && (
             <p style={{ color: 'red' }}>Error: {status.error}</p>
          )}
           {status.status === 'completed' && (
             <p style={{ color: 'green' }}>Upload complete! Processed {status.processed} files.</p>
          )}
        </div>
      )}
    </div>
  );
}

export default DocumentUploader;