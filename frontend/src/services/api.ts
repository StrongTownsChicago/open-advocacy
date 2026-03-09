import axios from 'axios';

// Get the base URL from environment variable or use default
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  paramsSerializer: {
    indexes: null,
  },
});

// Add request interceptor for debugging
api.interceptors.request.use(request => {
  return request;
});

// Add response interceptor for error handling
api.interceptors.response.use(
  response => {
    return response;
  },
  error => {
    console.error('API request failed:', error);
    return Promise.reject(error);
  }
);

api.interceptors.request.use(config => {
  // Force HTTPS for all requests
  if (config.url && config.url.startsWith('http://')) {
    config.url = config.url.replace('http://', 'https://');
  }
  return config;
});

export default api;
