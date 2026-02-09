import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { 
  User, 
  UserStats, 
  UserPreferences,
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
export function useUserStats() {
  return useQuery({
    queryKey: [...USER_QUERY_KEY, 'stats'],
    queryFn: async () => {
      const { data } = await api.get<UserStats>('/users/me/stats');
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
