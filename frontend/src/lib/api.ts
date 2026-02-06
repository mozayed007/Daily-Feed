import axios from 'axios';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
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
    console.error('API Error:', error.response?.data || error.message);
    
    // Handle specific error codes
    if (error.response?.status === 404) {
      console.error('Resource not found');
    } else if (error.response?.status === 422) {
      console.error('Validation error:', error.response.data.detail);
    }
    
    return Promise.reject(error);
  }
);
