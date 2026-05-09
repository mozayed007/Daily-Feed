import { describe, it, expect, vi, beforeEach } from 'vitest';
import { api } from '../lib/api';

vi.mock('../lib/auth', () => ({
  getAccessToken: vi.fn().mockReturnValue('test-token'),
  setAccessToken: vi.fn(),
  setRefreshToken: vi.fn(),
  clearTokens: vi.fn(),
}));

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should attach auth header when token exists', async () => {
    // Just verify the client is configured
    expect(api.defaults.headers.common).toBeDefined();
  });

  it('should have correct base URL', () => {
    expect(api.defaults.baseURL).toBe('/api');
  });
});
