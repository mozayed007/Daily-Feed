import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import { setAccessToken, setRefreshToken } from '../lib/auth';
import type { 
  User, 
  UserStats, 
  UserPreferencesResponse,
  UpdatePreferencesRequest,
  OnboardingRequest,
  RecordInteractionRequest,
  UserInteractionResponse
} from '../types/api';

const USER_QUERY_KEY = ['user'] as const;
const USER_PREFS_QUERY_KEY = ['preferences'] as const;

// Get current user
export function useUser() {
  return useQuery({
    queryKey: USER_QUERY_KEY,
    queryFn: async () => {
      const { data } = await api.get<User>('/users/me');
      return data;
    },
  });
}

// Get user stats
export function useUserStats(days = 7) {
  return useQuery({
    queryKey: [...USER_QUERY_KEY, 'stats', days],
    queryFn: async () => {
      const { data } = await api.get<UserStats>(`/users/me/stats?days=${days}`);
      return data;
    },
  });
}

// Complete onboarding
export function useOnboarding() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (data: OnboardingRequest) => {
      const response = await api.post<User>('/users/onboarding', data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY });
      queryClient.invalidateQueries({ queryKey: USER_PREFS_QUERY_KEY });
    },
  });
}

// Get preferences
export function usePreferences() {
  return useQuery({
    queryKey: USER_PREFS_QUERY_KEY,
    queryFn: async () => {
      const { data } = await api.get<UserPreferencesResponse>('/users/me/preferences');
      return data;
    },
  });
}

// Update preferences
export function useUpdatePreferences() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (prefs: UpdatePreferencesRequest) => {
      const { data } = await api.patch<UserPreferencesResponse>('/users/me/preferences', prefs);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: USER_PREFS_QUERY_KEY });
    },
  });
}

// Record article interaction
export function useRecordInteraction() {
  return useMutation({
    mutationFn: async (interaction: RecordInteractionRequest) => {
      const { data } = await api.post<UserInteractionResponse>('/users/me/interactions', interaction);
      return data;
    },
  });
}

// Get reading history
export function useReadingHistory(savedOnly = false, limit = 20) {
  return useQuery({
    queryKey: ['history', savedOnly, limit],
    queryFn: async () => {
      const { data } = await api.get(`/users/me/history?limit=${limit}&saved_only=${savedOnly}`);
      return data;
    },
  });
}

// Reset preferences
export function useResetPreferences() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async () => {
      await api.post('/users/me/preferences/reset');
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: USER_PREFS_QUERY_KEY });
    },
  });
}

// Change password
export function useChangePassword() {
  return useMutation({
    mutationFn: async (data: { current_password: string; new_password: string }) => {
      const { data: responseData } = await api.post('/users/me/password', data);
      return responseData;
    },
  });
}

// Email verification
export function useSendVerificationEmail() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post('/auth/verify-email');
      return data;
    },
  });
}

export function useConfirmEmail() {
  return useMutation({
    mutationFn: async (token: string) => {
      const { data } = await api.post('/auth/verify-email/confirm', { token });
      return data;
    },
  });
}

// OAuth
export function useOAuthUrl() {
  return useMutation({
    mutationFn: async (provider: 'google' | 'github') => {
      const { data } = await api.get(`/auth/oauth/${provider}`);
      return data as { auth_url: string; state: string };
    },
  });
}

export function useOAuthCallback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ code, provider }: { code: string; provider: string }) => {
      const { data } = await api.post('/auth/oauth/callback', { code, provider });
      return data as { access_token: string; refresh_token: string; token_type: string };
    },
    onSuccess: (data) => {
      setAccessToken(data.access_token);
      setRefreshToken(data.refresh_token);
      queryClient.invalidateQueries({ queryKey: USER_QUERY_KEY });
    },
  });
}
