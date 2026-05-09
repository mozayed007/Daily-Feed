import { useMutation, useQuery } from '@tanstack/react-query';
import {
  clusterArticles,
  synthesizeArticles,
  detectTrends,
  reasonArticleInclusion,
} from '@/lib/api';
import type {
  ClusterResponse,
  SynthesizeResponse,
  TrendsResponse,
  ReasoningResponse,
} from '@/types/api';

// ── Article Clustering ───────────────────────────────────────────────────────

export function useClusterArticles() {
  return useMutation<ClusterResponse, Error, { articleIds: number[] }>({
    mutationFn: ({ articleIds }) => clusterArticles(articleIds),
  });
}

// ── Multi-Source Synthesis ───────────────────────────────────────────────────

export function useSynthesizeArticles() {
  return useMutation<SynthesizeResponse, Error, { topic: string; articleIds: number[] }>({
    mutationFn: ({ topic, articleIds }) => synthesizeArticles(topic, articleIds),
  });
}

// ── Trend Detection ────────────────────────────────────────────────────────

export function useDetectTrends(articleIds?: number[]) {
  return useQuery<TrendsResponse, Error>({
    queryKey: ['trends', articleIds],
    queryFn: () => detectTrends(articleIds),
    enabled: false, // manual trigger only
  });
}

// ── Digest Reasoning ───────────────────────────────────────────────────────

export function useArticleReasoning() {
  return useMutation<ReasoningResponse, Error, number>({
    mutationFn: (articleId) => reasonArticleInclusion(articleId),
  });
}
