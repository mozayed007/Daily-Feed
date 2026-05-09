import { useState } from 'react';
import { TrendingUp, Zap, ArrowUpRight, ArrowDownRight, Minus, Activity, Brain } from 'lucide-react';
import { motion } from 'framer-motion';
import { useDetectTrends } from '@/hooks/useAI';
import { Skeleton } from '@/components/Skeleton';
import { EmptyState } from '@/components/EmptyState';
import { ErrorDisplay } from '@/components/ErrorDisplay';
import type { TrendResult } from '@/types/api';

const urgencyConfig = {
  high: { color: 'text-rose-600 dark:text-rose-400', bg: 'bg-rose-50 dark:bg-rose-900/20', icon: Zap },
  medium: { color: 'text-amber-600 dark:text-amber-400', bg: 'bg-amber-50 dark:bg-amber-900/20', icon: Activity },
  low: { color: 'text-emerald-600 dark:text-emerald-400', bg: 'bg-emerald-50 dark:bg-emerald-900/20', icon: TrendingUp },
};

const directionConfig = {
  rising: { icon: ArrowUpRight, color: 'text-emerald-600 dark:text-emerald-400', label: 'Rising' },
  falling: { icon: ArrowDownRight, color: 'text-rose-600 dark:text-rose-400', label: 'Falling' },
  stable: { icon: Minus, color: 'text-slate-500 dark:text-slate-400', label: 'Stable' },
  breaking: { icon: Zap, color: 'text-amber-600 dark:text-amber-400', label: 'Breaking' },
};

function TrendCard({ trend, index }: { trend: TrendResult; index: number }) {
  const urgency = urgencyConfig[trend.urgency] || urgencyConfig.medium;
  const direction = directionConfig[trend.trend_direction] || directionConfig.stable;
  const DirectionIcon = direction.icon;
  const UrgencyIcon = urgency.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: index * 0.1 }}
      className="bg-white dark:bg-slate-800 rounded-2xl border border-slate-200 dark:border-slate-700 p-5 hover:shadow-lg transition-shadow"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-semibold ${urgency.bg} ${urgency.color}`}>
            <UrgencyIcon className="w-3 h-3" />
            {trend.urgency}
          </span>
          <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs font-medium bg-slate-100 dark:bg-slate-700 ${direction.color}`}>
            <DirectionIcon className="w-3 h-3" />
            {direction.label}
          </span>
        </div>
        <span className="text-xs text-slate-500 dark:text-slate-400 font-medium">
          {trend.article_count} articles
        </span>
      </div>

      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
        {trend.topic}
      </h3>
      <p className="text-sm text-slate-600 dark:text-slate-300 mb-4 leading-relaxed">
        {trend.summary}
      </p>

      <div className="flex flex-wrap gap-2">
        {trend.top_sources.map((source) => (
          <span
            key={source}
            className="px-2 py-1 bg-blue-50 dark:bg-blue-900/20 text-blue-700 dark:text-blue-300 text-xs rounded-md font-medium"
          >
            {source}
          </span>
        ))}
      </div>
    </motion.div>
  );
}

export function Trends() {
  const [analyzed, setAnalyzed] = useState(false);
  const { data, isLoading, isError, error, refetch } = useDetectTrends();

  const handleDetect = async () => {
    setAnalyzed(true);
    await refetch();
  };

  const trends = data?.data || [];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <div className="w-10 h-10 bg-gradient-to-br from-violet-500 to-fuchsia-500 rounded-xl flex items-center justify-center shadow-lg shadow-violet-500/20">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">
              Trend Detection
            </h1>
            <p className="text-sm text-slate-500 dark:text-slate-400">
              AI-powered analysis of emerging topics across your feeds
            </p>
          </div>
        </div>
      </div>

      {!analyzed && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16"
        >
          <div className="w-20 h-20 bg-gradient-to-br from-violet-500/20 to-fuchsia-500/20 rounded-2xl flex items-center justify-center mx-auto mb-6">
            <TrendingUp className="w-10 h-10 text-violet-600 dark:text-violet-400" />
          </div>
          <h2 className="text-xl font-semibold text-slate-900 dark:text-white mb-2">
            Detect Emerging Trends
          </h2>
          <p className="text-slate-500 dark:text-slate-400 max-w-md mx-auto mb-6">
            Our AI analyzes your recent articles to identify rising topics, breaking stories,
            and emerging narratives across multiple sources.
          </p>
          <button
            onClick={handleDetect}
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-violet-600 to-fuchsia-600 text-white rounded-xl font-semibold hover:shadow-lg hover:shadow-violet-500/25 transition-all"
          >
            <Brain className="w-5 h-5" />
            Analyze Trends
          </button>
        </motion.div>
      )}

      {analyzed && isLoading && (
        <div className="grid gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      )}

      {analyzed && isError && (
        <ErrorDisplay
          title="Trend detection failed"
          message={error?.message || 'Unable to analyze trends'}
          onRetry={handleDetect}
        />
      )}

      {analyzed && !isLoading && !isError && trends.length === 0 && (
        <EmptyState
          icon={TrendingUp}
          title="No trends detected"
          description="There are not enough recent articles to identify trends. Try fetching more content first."
        />
      )}

      {analyzed && !isLoading && !isError && trends.length > 0 && (
        <div className="grid gap-4">
          {trends.map((trend, index) => (
            <TrendCard key={trend.topic} trend={trend} index={index} />
          ))}
        </div>
      )}
    </div>
  );
}
