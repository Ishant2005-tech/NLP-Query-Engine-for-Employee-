import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const connectDatabase = async (connectionString) => {
  const response = await api.post('/api/database/connect', {
    connection_string: connectionString,
    test_connection: true,
  });
  return response.data;
};

export const getSchema = async () => {
  const response = await api.get('/api/database/schema');
  return response.data;
};

export const uploadDocuments = async (files) => {
  const formData = new FormData();
  files.forEach((file) => {
    formData.append('files', file);
  });

  const response = await api.post('/api/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getIngestionStatus = async (jobId) => {
  const response = await api.get(`/api/documents/status/${jobId}`);
  return response.data;
};

export const processQuery = async (query) => {
  const response = await api.post('/api/query/', { query });
  return response.data;
};

export const getQueryHistory = async () => {
  const response = await api.get('/api/query/history');
  return response.data;
};

export default api;