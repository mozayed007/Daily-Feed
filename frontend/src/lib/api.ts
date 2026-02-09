import axios from 'axios';
import { events } from './events';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add request interceptor for auth (when you add it)
// api.interceptors.request.use((config) => {
//   const token = localStorage.getItem('token');
//   if (token) {
//     config.headers.Authorization = `Bearer ${token}`;
//   }
//   return config;
// });

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail;
    const message =
      typeof detail === 'string'
        ? detail
        : Array.isArray(detail)
          ? detail.map((item: any) => item?.msg || item).join(', ')
          : error.message || 'An unexpected error occurred.';
    console.error('API Error:', message);
    
    events.emit('toast', {
      type: 'error',
      title: 'API Error',
      message: typeof message === 'string' ? message : 'An unexpected error occurred.',
    });
    
    // Handle specific error codes
    if (error.response?.status === 404) {
      console.error('Resource not found');
    } else if (error.response?.status === 422) {
      console.error('Validation error:', error.response.data.detail);
    }
    
    return Promise.reject(error);
  }
);
