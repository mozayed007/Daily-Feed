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

// Get current user
export function useUser() {
  return useQuery({
    queryKey: ['user'],
    queryFn: async () => {
      // Check for stored user ID
      const userId = localStorage.getItem('current_user_id');
      const url = userId ? `/users/me?user_id=${userId}` : '/users/me';
      const { data } = await api.get<User>(url);
      
      // Store ID if not set (first load)
      if (!userId && data.id) {
        localStorage.setItem('current_user_id', data.id.toString());
      }
      return data;
    },
  });
}

// Get all users (for switching)
export function useAllUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: async () => {
      const { data } = await api.get<User[]>('/users');
      return data;
    },
  });
}

// Switch user
export function useSwitchUser() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async (userId: number) => {
      const { data } = await api.post<User>(`/users/switch/${userId}`);
      return data;
    },
    onSuccess: (data) => {
      localStorage.setItem('current_user_id', data.id.toString());
      queryClient.invalidateQueries(); // Refresh all data for new user
      window.location.reload(); // Hard reload to ensure clean state
    },
  });
}

// Get user stats
export function useUserStats() {
  return useQuery({
    queryKey: ['user', 'stats'],
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
      queryClient.invalidateQueries({ queryKey: ['user'] });
    },
  });
}

// Get preferences
export function usePreferences() {
  return useQuery({
    queryKey: ['preferences'],
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
      queryClient.invalidateQueries({ queryKey: ['preferences'] });
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
