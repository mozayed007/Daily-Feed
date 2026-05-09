import { motion } from 'framer-motion';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface ErrorDisplayProps {
  message: string;
  onRetry?: () => void;
  title?: string;
}

export function ErrorDisplay({ message, onRetry, title = 'Something went wrong' }: ErrorDisplayProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-slate-800 rounded-2xl p-6 border border-rose-200 dark:border-rose-900/40"
    >
      <div className="flex items-start gap-4">
        <div className="p-2 bg-rose-100 dark:bg-rose-900/30 rounded-lg">
          <AlertCircle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
        </div>
        <div className="flex-1">
          <h3 className="font-semibold text-rose-900 dark:text-rose-200">{title}</h3>
          <p className="text-sm text-rose-700 dark:text-rose-300 mt-1">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-4 inline-flex items-center gap-2 px-4 py-2 bg-rose-100 dark:bg-rose-900/30 text-rose-700 dark:text-rose-300 rounded-lg text-sm font-medium hover:bg-rose-200 dark:hover:bg-rose-900/50 transition-colors"
            >
              <RefreshCw className="w-4 h-4" />
              Try Again
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
