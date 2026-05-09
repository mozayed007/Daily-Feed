import { useQuery } from '@tanstack/react-query';
import { api } from '../lib/api';

export interface Category {
  name: string;
  count: number;
}

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: async () => {
      const { data } = await api.get<Category[]>('/articles/categories');
      return data;
    },
    staleTime: 5 * 60 * 1000,
  });
}
