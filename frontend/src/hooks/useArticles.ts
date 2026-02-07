import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { 
  ArticleListResponse, 
  ArticleFilterParams,
  PersonalizedDigest,
  ArticleFeedbackRequest 
} from '../types/api';

// Get articles list
export function useArticles(params: ArticleFilterParams = {}) {
  const searchParams = new URLSearchParams();
  if (params.page) {
    searchParams.set('page', params.page.toString());
  } else if (params.skip !== undefined && params.limit) {
    searchParams.set('page', Math.floor(params.skip / params.limit + 1).toString());
  }
  if (params.page_size) {
    searchParams.set('page_size', params.page_size.toString());
  } else if (params.limit) {
    searchParams.set('page_size', params.limit.toString());
  }
  if (params.processed !== undefined) searchParams.set('processed', params.processed.toString());
  if (params.category) searchParams.set('category', params.category);
  if (params.source) searchParams.set('source', params.source);

  return useQuery({
    queryKey: ['articles', params],
    queryFn: async () => {
      const { data } = await api.get<ArticleListResponse>(
        `/articles?${searchParams.toString()}`
      );
      return data;
    },
  });
}

// Get single article
export function useArticle(id: number) {
  return useQuery({
    queryKey: ['article', id],
    queryFn: async () => {
      const { data } = await api.get(`/articles/${id}`);
      return data;
    },
    enabled: !!id,
  });
}

// Generate personalized digest
export function useGenerateDigest() {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post<PersonalizedDigest>('/users/me/digest/generate');
      return data;
    },
  });
}

// Submit feedback (like/dislike/save)
export function useArticleFeedback() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: async ({ article_id, feedback }: ArticleFeedbackRequest) => {
      await api.post('/users/me/feedback', {
        article_id,
        feedback,
      });
    },
    onSuccess: () => {
      // Invalidate relevant queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      queryClient.invalidateQueries({ queryKey: ['digest'] });
    },
  });
}

// Summarize article
export function useSummarizeArticle() {
  return useMutation({
    mutationFn: async (articleId: number) => {
      const { data } = await api.post(`/articles/${articleId}/summarize`);
      return data;
    },
  });
}
