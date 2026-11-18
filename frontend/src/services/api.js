import axios from 'axios';

// In production, configure VITE_API_URL to point to your deployed backend (e.g. https://your-backend.onrender.com)
// In local development, defaults to '/api' which is proxied by Vite to http://127.0.0.1:8000
let rawApiUrl = import.meta.env.VITE_API_URL || '/api';
if (rawApiUrl && rawApiUrl.startsWith('http') && !rawApiUrl.endsWith('/api')) {
  rawApiUrl = `${rawApiUrl.replace(/\/+$/, '')}/api`;
}
const API_BASE_URL = rawApiUrl;

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Auth interceptor — attach JWT token
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor — handle 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token');
      localStorage.removeItem('user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

export default api;
