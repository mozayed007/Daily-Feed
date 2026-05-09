import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: {
    label: string;
    onClick: () => void;
  };
}

export function EmptyState({ icon: Icon, title, description, action }: EmptyStateProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white dark:bg-slate-800 rounded-2xl p-8 sm:p-12 border border-slate-200 dark:border-slate-700 text-center"
    >
      <div className="w-16 h-16 bg-slate-100 dark:bg-slate-700 rounded-2xl flex items-center justify-center mx-auto mb-4">
        <Icon className="w-8 h-8 text-slate-400 dark:text-slate-500" />
      </div>
      <h3 className="text-lg font-semibold text-slate-900 dark:text-white mb-2">
        {title}
      </h3>
      <p className="text-slate-500 dark:text-slate-400 mb-6 max-w-sm mx-auto">
        {description}
      </p>
      {action && (
        <button
          onClick={action.onClick}
          className="inline-flex items-center gap-2 px-4 py-2.5 bg-blue-600 text-white rounded-xl font-medium hover:bg-blue-700 transition-colors"
        >
          {action.label}
        </button>
      )}
    </motion.div>
  );
}
