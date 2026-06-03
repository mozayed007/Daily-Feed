import axios from 'axios';
import { getAccessToken, setAccessToken, getRefreshToken, setRefreshToken } from './auth';
import { events } from './events';

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use(
  (config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function normalizeApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError(error)) {
    const detail = error.response?.data?.detail;
    if (typeof detail === 'string' && detail.trim()) {
      return detail;
    }
    if (Array.isArray(detail) && detail.length > 0) {
      return detail.map((item: unknown) => (item as { msg?: string })?.msg || String(item)).join(', ');
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

async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = getRefreshToken();
  if (!refreshToken) return null;

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}/auth/refresh`,
      { refresh_token: refreshToken },
      { timeout: 10000 }
    );
    const { access_token, refresh_token } = response.data;
    setAccessToken(access_token);
    if (refresh_token) {
      setRefreshToken(refresh_token);
    }
    return access_token;
  } catch {
    setAccessToken(null);
    setRefreshToken(null);
    return null;
  }
}

// ── AI Features ──────────────────────────────────────────────────────────────

export async function clusterArticles(articleIds: number[]) {
  const { data } = await api.post('/articles/cluster', { article_ids: articleIds });
  return data;
}

export async function synthesizeArticles(topic: string, articleIds: number[]) {
  const { data } = await api.post('/articles/synthesize', { topic, article_ids: articleIds });
  return data;
}

export async function detectTrends(articleIds?: number[]) {
  const params = articleIds ? { article_ids: articleIds.join(',') } : {};
  const { data } = await api.get('/articles/trends', { params });
  return data;
}

export async function reasonArticleInclusion(articleId: number) {
  const { data } = await api.post(`/articles/${articleId}/reason`);
  return data;
}

// ── Voice Assistant ─────────────────────────────────────────────────────────

export async function sendVoiceCommand(text: string, voice?: string) {
  const { data } = await api.post('/voice/command', { text, voice });
  return data;
}

export async function speakText(text: string, voice?: string) {
  const { data } = await api.post('/voice/speak', { text, voice });
  return data;
}

export async function getVoiceStatus() {
  const { data } = await api.get('/voice/status');
  return data;
}

export async function stopVoiceAssistant() {
  const { data } = await api.post('/voice/stop');
  return data;
}

export function createVoiceWebSocket(): WebSocket {
  const baseUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
  const wsUrl = baseUrl.replace(/^http/, 'ws') + '/ws/voice';
  return new WebSocket(wsUrl);
}

// Add response interceptor for error handling and token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve) => {
          addRefreshSubscriber((token: string) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            resolve(api(originalRequest));
          });
        });
      }

      originalRequest._retry = true;
      isRefreshing = true;

      const newToken = await refreshAccessToken();
      isRefreshing = false;

      if (newToken) {
        onTokenRefreshed(newToken);
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return api(originalRequest);
      }

      setAccessToken(null);
      setRefreshToken(null);
      window.location.href = '/login';
      return Promise.reject(error);
    }

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
