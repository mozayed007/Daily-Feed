import { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowLeft,
  ExternalLink,
  Clock,
  ThumbsUp,
  ThumbsDown,
  Bookmark,
  Share2,
  Tag,
  Newspaper,
  BarChart3,
} from 'lucide-react';
import { useArticle } from '../hooks/useArticles';
import { useArticleFeedback } from '../hooks/useArticles';
import { useRecordInteraction } from '../hooks/useUser';
import { ArticleCardSkeleton, ChartSkeleton } from '../components/Skeleton';
import { ErrorDisplay } from '../components/ErrorDisplay';
import { events } from '../lib/events';

export function ArticleDetail() {
  const { id } = useParams<{ id: string }>();
  const articleId = id ? Number(id) : 0;

  const { data: article, isLoading, isError } = useArticle(articleId);
  const feedback = useArticleFeedback();
  const recordInteraction = useRecordInteraction();

  const [scrollDepth, setScrollDepth] = useState(0);
  const [timeOnPage, setTimeOnPage] = useState(0);
  const startTimeRef = useRef(Date.now());
  const containerRef = useRef<HTMLDivElement>(null);
  const hasRecordedRef = useRef(false);

  // Record that article was opened
  useEffect(() => {
    if (!articleId || hasRecordedRef.current) return;
    hasRecordedRef.current = true;

    recordInteraction.mutate({
      article_id: articleId,
      opened: true,
      read_duration_seconds: 0,
      scroll_depth: 0,
    });
  }, [articleId, recordInteraction]);

  // Track scroll depth
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleScroll = () => {
      const scrollTop = container.scrollTop;
      const scrollHeight = container.scrollHeight - container.clientHeight;
      if (scrollHeight > 0) {
        const depth = Math.min(scrollTop / scrollHeight, 1);
        setScrollDepth((prev) => Math.max(prev, depth));
      }
    };

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, []);

  // Track time on page
  useEffect(() => {
    const interval = setInterval(() => {
      setTimeOnPage(Math.floor((Date.now() - startTimeRef.current) / 1000));
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  // Send interaction on unmount
  useEffect(() => {
    return () => {
      if (articleId && timeOnPage > 0) {
        recordInteraction.mutate({
          article_id: articleId,
          read_duration_seconds: timeOnPage,
          scroll_depth: Math.round(scrollDepth * 100) / 100,
        });
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [articleId]);

  const handleFeedback = (type: 'like' | 'dislike' | 'save') => {
    feedback.mutate(
      { article_id: articleId, feedback: type },
      {
        onSuccess: () => {
          events.emit('toast', {
            type: 'success',
            title: type === 'save' ? 'Saved' : type === 'like' ? 'Liked' : 'Disliked',
            message: `Article ${type === 'save' ? 'saved to your reading list' : `marked as ${type}d`}.`,
            duration: 2000,
          });
        },
        onError: () => {
          events.emit('toast', {
            type: 'error',
            title: 'Error',
            message: 'Failed to save feedback. Please try again.',
            duration: 3000,
          });
        },
      }
    );
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="flex items-center gap-2 mb-4">
          <ArrowLeft className="w-5 h-5 text-slate-400" />
          <div className="h-4 w-24 bg-slate-100 dark:bg-slate-700 rounded animate-pulse" />
        </div>
        <ArticleCardSkeleton />
        <ChartSkeleton />
      </div>
    );
  }

  if (isError || !article) {
    return (
      <div className="space-y-6">
        <Link
          to="/"
          className="inline-flex items-center gap-2 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors mb-4"
        >
          <ArrowLeft className="w-5 h-5" />
          Back to Feed
        </Link>
        <ErrorDisplay message="Failed to load article. It may have been removed or the link is invalid." />
      </div>
    );
  }

  const publishedDate = article.published_at
    ? new Date(article.published_at).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
      })
    : null;

  return (
    <div className="space-y-6" ref={containerRef}>
      {/* Back Link */}
      <Link
        to="/"
        className="inline-flex items-center gap-2 text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 transition-colors"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Feed
      </Link>

      {/* Article Header */}
      <motion.article
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="bg-white dark:bg-slate-800 rounded-2xl p-6 sm:p-8 shadow-sm border border-slate-100 dark:border-slate-700"
      >
        <div className="flex flex-wrap items-center gap-3 mb-4">
          {article.category && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded-lg text-sm font-medium">
              <Tag className="w-3.5 h-3.5" />
              {article.category}
            </span>
          )}
          {article.sentiment && (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 rounded-lg text-sm font-medium">
              {article.sentiment}
            </span>
          )}
          <span className="inline-flex items-center gap-1 px-3 py-1 bg-slate-50 dark:bg-slate-700 text-slate-600 dark:text-slate-400 rounded-lg text-sm">
            <Newspaper className="w-3.5 h-3.5" />
            {article.source}
          </span>
        </div>

        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 dark:text-white mb-4 leading-tight">
          {article.title}
        </h1>

        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-500 dark:text-slate-400 mb-6">
          {publishedDate && (
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {publishedDate}
            </span>
          )}
          <span className="flex items-center gap-1">
            <BarChart3 className="w-4 h-4" />
            {article.reading_time || 1} min read
          </span>
        </div>

        {/* Summary */}
        {article.summary && (
          <div className="bg-blue-50 dark:bg-blue-900/20 border-l-4 border-blue-500 p-4 rounded-r-xl mb-6">
            <p className="text-slate-700 dark:text-slate-300 italic leading-relaxed">
              {article.summary}
            </p>
          </div>
        )}

        {/* Content */}
        {article.content && (
          <div
            className="prose dark:prose-invert max-w-none text-slate-700 dark:text-slate-300 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: article.content }}
          />
        )}

        {/* Key Points */}
        {article.key_points && article.key_points.length > 0 && (
          <div className="mt-6">
            <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-3">
              Key Points
            </h3>
            <ul className="space-y-2">
              {article.key_points.map((point, index) => (
                <li
                  key={index}
                  className="flex items-start gap-2 text-slate-700 dark:text-slate-300"
                >
                  <span className="w-5 h-5 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-full flex items-center justify-center text-xs font-medium shrink-0 mt-0.5">
                    {index + 1}
                  </span>
                  {point}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-3 mt-8 pt-6 border-t border-slate-100 dark:border-slate-700">
          <button
            onClick={() => handleFeedback('like')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-emerald-100 dark:hover:bg-emerald-900/30 hover:text-emerald-600 dark:hover:text-emerald-400 transition-colors"
          >
            <ThumbsUp className="w-4 h-4" />
            Like
          </button>
          <button
            onClick={() => handleFeedback('dislike')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-rose-100 dark:hover:bg-rose-900/30 hover:text-rose-600 dark:hover:text-rose-400 transition-colors"
          >
            <ThumbsDown className="w-4 h-4" />
            Dislike
          </button>
          <button
            onClick={() => handleFeedback('save')}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-amber-100 dark:hover:bg-amber-900/30 hover:text-amber-600 dark:hover:text-amber-400 transition-colors"
          >
            <Bookmark className="w-4 h-4" />
            Save
          </button>
          <a
            href={article.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-slate-100 dark:bg-slate-700 text-slate-700 dark:text-slate-300 hover:bg-blue-100 dark:hover:bg-blue-900/30 hover:text-blue-600 dark:hover:text-blue-400 transition-colors ml-auto"
          >
            <ExternalLink className="w-4 h-4" />
            Original
          </a>
        </div>
      </motion.article>
    </div>
  );
}
