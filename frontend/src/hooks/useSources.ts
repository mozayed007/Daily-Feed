import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface Source {
  id: number;
  name: string;
  url: string;
  category?: string;
  enabled: boolean;
  last_fetch?: string;
  fetch_count: number;
  error_count: number;
  created_at: string;
}

export function useSources() {
  return useQuery({
    queryKey: ['sources'],
    queryFn: async () => {
      const { data } = await api.get<Source[]>('/sources');
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}
