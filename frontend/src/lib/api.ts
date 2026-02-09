import axios from 'axios';
import { events } from './events';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

function normalizeApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((item: any) => item?.msg || String(item)).join(', ');
    }
    if (error.code === 'ECONNABORTED') {
      return 'Request timed out. Please try again.';
    }
    if (!error.response) {
      return 'Unable to reach the API server.';
    }
    return error.message || 'Request failed.';
  }
  if (error instanceof Error) {
    return error.message;
  }
  return 'An unexpected error occurred.';
}

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = normalizeApiErrorMessage(error);
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
    } else if (error.code === 'ECONNABORTED') {
      console.error('Request timed out');
    }
    
    return Promise.reject(error);
  }
);
