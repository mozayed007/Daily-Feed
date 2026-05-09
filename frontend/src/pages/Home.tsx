import { useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  ThumbsUp,
  ThumbsDown,
  Bookmark,
  X,
  Sparkles,
  Clock,
  TrendingUp,
  BookOpen,
  RefreshCw,
  ChevronDown,
  ExternalLink,
  Newspaper,
} from 'lucide-react';
import { useArticles, useGenerateDigest, useArticleFeedback, useSearchArticles } from '../hooks/useArticles';
import { useUserStats } from '../hooks/useUser';
import type { Article, PersonalizedArticle } from '../types/api';
import { ArticleCardSkeleton } from '../components/Skeleton';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { EmptyState } from '../components/EmptyState';

export function Home() {
  const [showDigest, setShowDigest] = useState(false);
  const { data: articles, isLoading: articlesLoading, isError: articlesError } = useArticles({ limit: 10 });
  const { data: stats, isError: statsError } = useUserStats();
  const generateDigest = useGenerateDigest();
  const feedback = useArticleFeedback();
  const [digestError, setDigestError] = useState<string | null>(null);

  const handleGenerateDigest = () => {
    generateDigest.mutate();
    setDigestError(null);
    setShowDigest(true);
  };

  const handleDigestError = (error: unknown) => {
    console.error('Digest generation failed:', error);
    
    if (error instanceof Error) {
      if (error.message.includes('Network')) {
        setDigestError('Network connection failed. Please check your internet connection.');
      } else if (error.message.includes('404') || error.message.includes('Not Found')) {
        setDigestError('Could not generate digest. Please try again later.');
      } else if (error.message.includes('500') || error.message.includes('Server Error')) {
        setDigestError('Server error occurred. Please try again later.');
      } else {
        setDigestError('An unexpected error occurred. Please try again.');
      }
    } else {
      setDigestError('An unexpected error occurred. Please try again.');
    }
  };

  const resetDigestError = () => {
    setDigestError(null);
    setShowDigest(false);
  };

  const handleRetry = () => {
    generateDigest.mutate();
    setDigestError(null);
  };

  const handleFeedback = (articleId: string | number, type: 'like' | 'dislike' | 'save') => {
    feedback.mutate({ article_id: Number(articleId), feedback: type });
  };

  const [searchQuery, setSearchQuery] = useState('');
  const { data: searchResults, isLoading: searchLoading } = useSearchArticles(searchQuery);

  return (
    <div className="space-y-8">
      {/* Welcome Section */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-6 sm:p-8 text-white relative overflow-hidden"
      >
        <div className="absolute top-0 right-0 w-80 h-80 bg-white/20 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl animate-pulse" />
        <div className="absolute bottom-0 left-0 w-64 h-64 bg-white/10 rounded-full translate-y-1/2 -translate-x-1/2 blur-2xl" />
        
        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">
          <div className="space-y-4 text-center md:text-left">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/20 backdrop-blur-md border border-white/20 text-xs font-bold uppercase tracking-widest">
              <Sparkles className="w-3.5 h-3.5 text-amber-300" />
              Intelligence Engine Active
            </div>
            <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight">
              Curated for <span className="text-amber-200">Growth.</span>
            </h1>
            <p className="text-primary-foreground/90 max-w-md text-lg font-medium leading-relaxed">
              You&apos;ve processed {stats?.total_articles_read || 0} signals this week. 
              Ready for your tactical session?
            </p>
          </div>

          <button
            onClick={handleGenerateDigest}
            disabled={generateDigest.isPending}
            className="flex-shrink-0 group relative overflow-hidden bg-white text-primary px-10 py-5 rounded-[2rem] font-bold text-lg hover:bg-slate-50 transition-all shadow-2xl hover:scale-105 active:scale-95"
          >
            {generateDigest.isPending ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                Generate Today&apos;s Digest
              </>
            )}
            {generateDigest.isError && (
              <span className="ml-2 text-xs text-rose-500">⚠️</span>
            )}
            {digestError && (
              <span className="ml-2 text-xs text-rose-500">⚠️</span>
            )}
          </button>
        </div>
      </motion.div>

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {[
          {
            icon: BookOpen,
            label: 'Processed',
            value: stats?.total_articles_read || 0,
            styles: { bg: 'bg-primary/10 text-primary' },
          },
          {
            icon: Bookmark,
            label: 'Tactical',
            value: stats?.total_articles_saved || 0,
            styles: { bg: 'bg-amber-500/10 text-amber-500' },
          },
          {
            icon: Clock,
            label: 'Velocity',
            value: `${Math.round((stats?.average_reading_time || 0) / 60)}m`,
            styles: { bg: 'bg-emerald-500/10 text-emerald-500' },
          },
          {
            icon: TrendingUp,
            label: 'Precision',
            value: `${stats?.digest_open_rate || 0}%`,
            styles: { bg: 'bg-violet-500/10 text-violet-500' },
          },
        ].map((stat, index) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 + index * 0.05 }}
            className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-5 shadow-sm border border-slate-100 dark:border-slate-700 transition-colors"
          >
            <div className={`w-10 h-10 rounded-xl bg-blue-50 dark:bg-blue-900/30 flex items-center justify-center mb-3`}>
              <stat.icon className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            </div>
            <p className="text-3xl font-black tracking-tight text-foreground">{stat.value}</p>
            <p className="text-xs font-bold uppercase tracking-widest text-muted-foreground mt-1">{stat.label}</p>
          </motion.div>
        ))}
      </div>

      {/* Generated Digest */}
      <AnimatePresence>
        {showDigest && generateDigest.data && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="bg-gradient-to-br from-violet-50 to-purple-50 rounded-3xl p-1"
          >
            <div className="bg-white/80 dark:bg-slate-800/80 backdrop-blur rounded-[22px] p-6 transition-colors">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2 transition-colors">
                    <Sparkles className="w-5 h-5 text-violet-600 dark:text-violet-400" />
                    Your Personalized Digest
                  </h2>
                  <p className="text-sm text-slate-500 dark:text-slate-400 transition-colors">
                    Match Score: {' '}
                    <span className="font-semibold text-violet-600 dark:text-violet-400">
                      {(generateDigest.data.personalization_score * 100).toFixed(0)}%
                    </span>
                  </p>
                </div>
                <button
                  onClick={() => setShowDigest(false)}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                  <X className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                </button>
              </div>

              <div className="space-y-3">
                {generateDigest.data.articles.slice(0, 5).map((article: PersonalizedArticle, index: number) => (
                  <motion.div
                    key={article.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center gap-4 p-4 bg-white dark:bg-slate-800/50 rounded-xl shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-all"
                  >
                    <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-violet-100 to-purple-100 dark:from-violet-900/50 dark:to-purple-900/50 rounded-xl flex items-center justify-center">
                      <span className="text-lg font-bold text-violet-600 dark:text-violet-400">#{index + 1}</span>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-slate-900 dark:text-white truncate transition-colors">{article.title}</h3>
                      <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                        <span>{article.source}</span>
                        <span>•</span>
                        <span className="text-violet-600 dark:text-violet-400 font-medium">Score: {(article.score * 100).toFixed(0)}%</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={() => handleFeedback(article.id, 'like')}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                      >
                        <ThumbsUp className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                      </button>
                      <button
                        onClick={() => handleFeedback(article.id, 'save')}
                        className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                      >
                        <Bookmark className="w-4 h-4 text-slate-400 dark:text-slate-500" />
                      </button>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
      {showDigest && generateDigest.isError && (
        <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-rose-200 dark:border-rose-900/40 text-rose-600 dark:text-rose-300">
          We couldn&apos;t generate a digest right now. Please try again.
        </div>
      )}
      {showDigest && digestError && (
        <ErrorDisplay
          message={digestError}
          onRetry={handleRetry}
        />
      )}

      {/* Search Bar */}
      <div className="relative">
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search articles..."
          className="w-full pl-4 pr-10 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {searchLoading && (
          <div className="absolute right-3 top-1/2 -translate-y-1/2">
            <RefreshCw className="w-5 h-5 text-slate-400 animate-spin" />
          </div>
        )}
      </div>

      {/* Recent Articles */}
      <div>
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-bold text-slate-900 dark:text-white transition-colors">
            {searchQuery ? `Search Results (${searchResults?.total ?? 0})` : 'Recent Articles'}
          </h2>
          <button className="text-sm text-blue-600 dark:text-blue-400 font-medium flex items-center gap-1 hover:underline">
            View all
            <ChevronDown className="w-4 h-4 -rotate-90" />
          </button>
        </div>

        {articlesLoading || searchLoading ? (
          <div className="space-y-4">
            {[1, 2, 3].map((i) => (
              <ArticleCardSkeleton key={i} />
            ))}
          </div>
        ) : articlesError || statsError ? (
          <ErrorDisplay
            message="We couldn't load your feed right now. Please try again in a moment."
            onRetry={() => {
              window.location.reload();
            }}
          />
        ) : searchQuery && !searchResults?.articles?.length ? (
          <div className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-300">
            No articles found for &quot;{searchQuery}&quot;. Try a different search term.
          </div>
        ) : !searchQuery && !articles?.articles?.length ? (
          <EmptyState
            icon={Newspaper}
            title="No articles yet"
            description="Articles will appear once the pipeline fetches and processes them. Try generating a digest or check back later."
          />
        ) : (
          <div className="space-y-4">
            {(searchQuery ? searchResults?.articles : articles?.articles)?.map((article, index) => (
              <ArticleCard
                key={article.id}
                article={article}
                index={index}
                onFeedback={handleFeedback}
              />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface ArticleCardProps {
  article: Article | PersonalizedArticle;
  index: number;
  onFeedback: (articleId: string | number, type: 'like' | 'dislike' | 'save') => void;
}

function ArticleCard({ article, index, onFeedback }: ArticleCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [liked, setLiked] = useState(false);
  const [saved, setSaved] = useState(false);
  const [disliked, setDisliked] = useState(false);

  const handleLike = () => {
    setLiked(!liked);
    setDisliked(false);
    onFeedback(article.id, 'like');
  };

  const handleDislike = () => {
    setDisliked(!disliked);
    setLiked(false);
    onFeedback(article.id, 'dislike');
  };

  const handleSave = () => {
    setSaved(!saved);
    onFeedback(article.id, 'save');
  };

  const categoryColors: Record<string, string> = {
    AI: 'bg-violet-100 dark:bg-violet-900/30 text-violet-700 dark:text-violet-300',
    Technology: 'bg-cyan-100 dark:bg-cyan-900/30 text-cyan-700 dark:text-cyan-300',
    Business: 'bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300',
    Science: 'bg-emerald-100 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300',
    Crypto: 'bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300',
  };

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05 }}
      className="bg-white dark:bg-slate-800 rounded-2xl p-4 sm:p-6 shadow-sm border border-slate-100 dark:border-slate-700 hover:shadow-md transition-all"
    >
      <div className="flex items-start gap-3 sm:gap-4">
        {/* Source Avatar */}
        <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-slate-100 to-slate-200 dark:from-slate-700 dark:to-slate-600 rounded-xl flex items-center justify-center text-sm font-bold text-slate-600 dark:text-slate-300 transition-colors">
          {article.source?.slice(0, 2).toUpperCase()}
        </div>

        <div className="flex-1 min-w-0">
          {/* Meta */}
          <div className="flex flex-wrap items-center gap-2 mb-2">
            {article.category && (
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full ${categoryColors[article.category] || 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'}`}>
                {article.category}
              </span>
            )}
            <span className="text-xs text-slate-400 dark:text-slate-500">{article.source}</span>
            {article.reading_time && (
              <span className="text-xs text-slate-400 dark:text-slate-500 flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {article.reading_time} min
              </span>
            )}
          </div>

          {/* Title */}
          <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2 hover:text-blue-600 dark:hover:text-blue-400 transition-colors cursor-pointer">
            <Link to={`/articles/${article.id}`}>
              {article.title}
            </Link>
          </h3>

          {/* Summary */}
          {article.summary && (
            <div className={`text-slate-600 dark:text-slate-300 text-sm leading-relaxed ${expanded ? '' : 'line-clamp-2'}`}>
              {article.summary}
            </div>
          )}

          {/* Key Points */}
          {article.key_points && article.key_points.length > 0 && expanded && (
            <ul className="mt-3 space-y-2">
              {article.key_points.map((point: string, i: number) => (
                <li key={i} className="flex items-start gap-2 text-sm text-slate-600 dark:text-slate-300">
                  <span className="w-1.5 h-1.5 bg-blue-400 dark:bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                  {point}
                </li>
              ))}
            </ul>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between mt-4 pt-4 border-t border-slate-100 dark:border-slate-700">
            <div className="flex items-center gap-1">
              <ActionButton
                onClick={handleLike}
                active={liked}
                activeColor="text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/30"
                icon={ThumbsUp}
                label="Like"
              />
              <ActionButton
                onClick={handleDislike}
                active={disliked}
                activeColor="text-rose-600 dark:text-rose-400 bg-rose-50 dark:bg-rose-900/30"
                icon={ThumbsDown}
                label="Dislike"
              />
              <ActionButton
                onClick={handleSave}
                active={saved}
                activeColor="text-amber-600 dark:text-amber-400 bg-amber-50 dark:bg-amber-900/30"
                icon={Bookmark}
                label="Save"
              />
            </div>

            <div className="flex items-center gap-2">
              {article.summary && (
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 font-medium cursor-pointer z-10"
                >
                  {expanded ? 'Show less' : 'Read more'}
                </button>
              )}
              <a
                href={article.url}
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
              >
                <ExternalLink className="w-4 h-4" />
              </a>
            </div>
          </div>
        </div>
      </div>
    </motion.article>
  );
}

interface ActionButtonProps {
  onClick: () => void;
  active: boolean;
  activeColor: string;
  icon: React.ElementType;
  label: string;
}

function ActionButton({ onClick, active, activeColor, icon: Icon, label }: ActionButtonProps) {
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-1.5 px-3 py-2.5 min-h-[44px] rounded-lg text-sm font-medium transition-all ${
        active
          ? activeColor
          : 'text-slate-500 dark:text-slate-400 hover:bg-slate-100 dark:hover:bg-slate-700 active:bg-slate-200 dark:active:bg-slate-600'
      }`}
    >
      <Icon className="w-4 h-4" />
      <span className="hidden sm:inline">{active ? label : ''}</span>
    </button>
  );
}