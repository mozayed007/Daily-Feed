import { useState } from 'react';
import { motion } from 'framer-motion';
import { Bookmark, Clock, Calendar, ChevronRight, Filter } from 'lucide-react';
import { useReadingHistory } from '../hooks/useUser';
import { useArticles } from '../hooks/useArticles';

export function History() {
  const [activeTab, setActiveTab] = useState<'all' | 'saved'>('all');
  const { data: history } = useReadingHistory(activeTab === 'saved', 50);
  const { data: articles } = useArticles({ limit: 50 });

  // Merge history with article details
  const historyWithArticles = history?.map((h: any) => ({
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
        <div className="flex p-1 bg-slate-100 dark:bg-slate-700 rounded-xl transition-colors">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                activeTab === tab.id
                  ? 'bg-white dark:bg-slate-600 text-slate-900 dark:text-white shadow-sm'
                  : 'text-slate-600 dark:text-slate-300 hover:text-slate-900 dark:hover:text-white'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* History List */}
      <div className="space-y-3">
        {historyWithArticles?.length === 0 && (
          <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-2xl border border-slate-100 dark:border-slate-700 transition-colors">
            <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-full flex items-center justify-center mx-auto mb-4">
              <Filter className="w-8 h-8 text-slate-400 dark:text-slate-500" />
            </div>
            <h3 className="font-medium text-slate-900 dark:text-white transition-colors">No articles yet</h3>
            <p className="text-sm text-slate-500 dark:text-slate-400 mt-1 transition-colors">
              {activeTab === 'saved'
                ? "Articles you save will appear here"
                : "Start reading articles to see your history"}
            </p>
          </div>
        )}

        {historyWithArticles?.map((item: any, index: number) => (
          <motion.div
            key={item.id}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            className="bg-white dark:bg-slate-800 rounded-2xl p-5 shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-all cursor-pointer group"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  {item.article?.category && (
                    <span className="text-xs font-medium px-2 py-0.5 bg-slate-100 rounded-full text-slate-600">
                      {item.article.category}
                    </span>
                  )}
                  <span className="text-xs text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3" />
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                  {item.saved && (
                    <span className="text-xs font-medium px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full flex items-center gap-1">
                      <Bookmark className="w-3 h-3" />
                      Saved
                    </span>
                  )}
                </div>

                <h3 className="font-semibold text-slate-900 group-hover:text-blue-600 transition-colors">
                  {item.article?.title || 'Unknown Article'}
                </h3>

                <div className="flex items-center gap-4 mt-2 text-sm text-slate-500">
                  <span>{item.article?.source}</span>
                  {item.read_duration_seconds > 0 && (
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      {Math.round(item.read_duration_seconds / 60)}m read
                    </span>
                  )}
                  {item.rating === 1 && <span className="text-emerald-600">Liked</span>}
                  {item.rating === -1 && <span className="text-rose-600">Disliked</span>}
                </div>
              </div>

              <ChevronRight className="w-5 h-5 text-slate-300 group-hover:text-blue-600 transition-colors" />
            </div>
          </motion.div>
        ))}
      </div>
    </div>
  );
}
