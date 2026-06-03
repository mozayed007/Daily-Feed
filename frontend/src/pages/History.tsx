import { useState } from 'react';
import { motion } from 'framer-motion';
import { Bookmark, Clock, Calendar, ChevronRight } from 'lucide-react';
import { useReadingHistory } from '../hooks/useUser';
import { useArticles } from '../hooks/useArticles';
import { ArticleCardSkeleton } from '../components/Skeleton';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { EmptyState } from '../components/EmptyState';

interface HistoryItem {
  id: string;
  article_id: number;
  read_duration_seconds?: number;
  read_duration?: number;
  rating?: number;
  saved: boolean;
  created_at: string;
}

export function History() {
  const [activeTab, setActiveTab] = useState<'all' | 'saved'>('all');
  const { data: history, isLoading: historyLoading, isError: historyError, refetch: refetchHistory } = useReadingHistory(activeTab === 'saved', 50);
  const { data: articles, isError: articlesError, refetch: refetchArticles } = useArticles({ limit: 50 });

  const handleRetry = () => {
    refetchHistory();
    refetchArticles();
  };

  // Merge history with article details
  const historyWithArticles = history?.map((h: HistoryItem) => ({
    ...h,
    article: articles?.articles.find((a) => a.id === h.article_id),
  }));

  const tabs = [
    { id: 'all', label: 'All History', icon: Clock },
    { id: 'saved', label: 'Saved Articles', icon: Bookmark },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white transition-colors">Reading History</h1>
          <p className="text-slate-500 dark:text-slate-400 transition-colors">Track your reading journey</p>
        </div>

        {/* Tabs */}
        <div className="flex p-1 bg-slate-100 dark:bg-slate-700 rounded-xl transition-colors overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as 'all' | 'saved')}
              className={`flex items-center gap-2 px-3 sm:px-4 py-2 rounded-lg text-sm font-medium transition-all whitespace-nowrap min-h-[44px] ${
                activeTab === tab.id
                  ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              <span className="hidden sm:inline">{tab.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* History List */}
      <div className="space-y-3">
        {historyLoading && (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <ArticleCardSkeleton key={i} />
            ))}
          </div>
        )}

        {(historyError || articlesError) && (
          <ErrorDisplay
            message="Couldn't load history right now. Please refresh and try again."
            onRetry={handleRetry}
          />
        )}

        {!historyLoading && !historyError && historyWithArticles?.length === 0 && (
          <EmptyState
            icon={activeTab === 'saved' ? Bookmark : Clock}
            title={activeTab === 'saved' ? 'No saved articles' : 'No reading history'}
            description={
              activeTab === 'saved'
                ? 'Articles you save will appear here. Start exploring your feed!'
                : 'Start reading articles to see your history. Every read counts!'
            }
          />
        )}

        {!historyLoading && !historyError && historyWithArticles?.map((item: HistoryItem & { article?: { id: number; title?: string; source?: string; category?: string } }, index: number) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-all cursor-pointer group"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {item.article?.category && (
                    <span className="text-xs font-medium px-2 py-0.5 bg-slate-100 dark:bg-slate-700 rounded-full text-slate-600 dark:text-slate-300 transition-colors">
                      {item.article.category}
                    </span>
                  )}
                  <span className="text-xs text-slate-400 dark:text-slate-500 flex items-center gap-1 transition-colors">
                    <Calendar className="w-3 h-3" />
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                  {item.saved && (
                    <span className="text-xs font-medium px-2 py-0.5 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-400 rounded-full flex items-center gap-1 transition-colors">
                      <Bookmark className="w-3 h-3" />
                      Saved
                    </span>
                  )}
                </div>

                <h3 className="font-semibold text-slate-900 dark:text-white group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
                  {item.article?.title || 'Unknown Article'}
                </h3>

                <div className="flex items-center gap-4 mt-2 text-sm text-slate-500 dark:text-slate-400 transition-colors">
                  <span>{item.article?.source}</span>
                  {((item.read_duration_seconds ?? item.read_duration ?? 0) > 0) && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {Math.round((item.read_duration_seconds ?? item.read_duration ?? 0) / 60)}m read
                    </span>
                  )}
                  {item.rating === 1 && <span className="text-emerald-600 dark:text-emerald-400">Liked</span>}
                  {item.rating === -1 && <span className="text-rose-600 dark:text-rose-400">Disliked</span>}
                </div>
              </div>

              <ChevronRight className="w-5 h-5 text-slate-300 dark:text-slate-600 group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors" />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
